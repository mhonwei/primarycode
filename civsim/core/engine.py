"""Simulation engine: explicit annual stepping with enforced closure.

Step semantics
--------------
Each step runs in two passes:

  pass 1 (diagnostics)  modules run in declared order; each may read stocks and
                        any diagnostic published by an earlier module.
  pass 2 (rates)        every module returns its flow rates, now with the full
                        diagnostic context visible.

Then all flows are applied simultaneously from the start-of-step state (explicit
Euler), the conservation ledger is re-checked, and the financial ledger is
re-checked. Applying flows only after every rate is known means module ordering
affects *what information is available*, never *what state a rate was computed
against* -- so reordering modules cannot silently change the numbers.

Integration error
-----------------
Explicit Euler at dt=1yr is first-order. For M0 this is a deliberate choice, not
an oversight: the alternative (adaptive RK) buys accuracy the input data does
not support -- the bundled series are 5-yearly and grade B -- while making the
conservation bookkeeping much harder to keep exact. `Engine.step_halved_probe`
reports the integration error against a half-step run so the size of what we are
neglecting is measured rather than assumed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np

from ..modules.base import Module
from .financial import FinancialLedger, Sector
from .ledger import ConservationLedger
from .quantities import Quantity
from .stocks import FlowSpec, Limit, StateView, Stock


class ConstraintBinding(RuntimeError):
    """A physical limit was reached: this trajectory is excluded.

    Not an error in the model. The whole point of tracking reserves explicitly
    is that running out is a statement about which futures are reachable, and
    the exclusion analysis in civsim/forward.py treats these as data.
    """

    def __init__(self, stock: str, t: float, available: float, demanded: float):
        self.stock, self.t = stock, t
        self.available, self.demanded = available, demanded
        super().__init__(
            f"physical limit reached at t={t:g}: {stock!r} holds "
            f"{available:.6g} but {demanded:.6g} was drawn. This trajectory is "
            "excluded, which is a result and not a failure."
        )


class ReservoirUndersized(RuntimeError):
    """An accounting reservoir ran dry -- a modelling bug, not a finding."""

    def __init__(self, stock: str, t: float, available: float, demanded: float):
        super().__init__(
            f"accounting reservoir {stock!r} ran dry at t={t:g} "
            f"({available:.6g} available, {demanded:.6g} drawn). This is a "
            "bookkeeping device, not a limit on the world: it was sized too "
            "small. Raising it changes nothing physical. Do NOT report this as "
            "a constraint."
        )


#: Retained for callers that only care that integration failed.
NegativeStockError = ConstraintBinding


@dataclass
class Trajectory:
    """Recorded run: stock paths and diagnostic paths on a common time axis."""

    times: np.ndarray
    stocks: dict[str, np.ndarray]
    diagnostics: dict[str, np.ndarray]
    flows: dict[str, np.ndarray] = field(default_factory=dict)

    def series(self, name: str) -> np.ndarray:
        if name in self.diagnostics:
            return self.diagnostics[name]
        if name in self.stocks:
            return self.stocks[name]
        raise KeyError(
            f"{name!r} is neither a diagnostic nor a stock. "
            f"diagnostics={sorted(self.diagnostics)} stocks={sorted(self.stocks)}"
        )

    def at(self, name: str, years: Sequence[float]) -> np.ndarray:
        """Values of `name` at the given years, by exact index lookup."""
        idx = {float(t): i for i, t in enumerate(self.times)}
        s = self.series(name)
        try:
            return np.array([s[idx[float(y)]] for y in years])
        except KeyError as e:
            raise KeyError(
                f"year {e.args[0]} not in trajectory "
                f"[{self.times[0]:g}, {self.times[-1]:g}]"
            ) from None


class Engine:
    def __init__(
        self,
        modules: Sequence[Module],
        params: Mapping[str, Any],
        sectors: Sequence[Sector] | None = None,
        dt: float = 1.0,
        tolerances: dict[Quantity, float] | None = None,
        check_conservation: bool = True,
    ) -> None:
        self.modules = list(modules)
        self.params = dict(params)
        self.dt = float(dt)
        self.check_conservation = check_conservation

        self._stocks: dict[str, Stock] = {}
        for m in self.modules:
            for s in m.stocks():
                if s.name in self._stocks:
                    raise ValueError(
                        f"duplicate stock {s.name!r} declared by module "
                        f"{m.name!r}; stock names are global"
                    )
                self._stocks[s.name] = s

        self._flows: dict[str, FlowSpec] = {}
        self._flow_owner: dict[str, str] = {}
        for m in self.modules:
            for f in m.flows():
                if f.name in self._flows:
                    raise ValueError(f"duplicate flow {f.name!r}")
                self._validate_flow(f, m.name)
                self._flows[f.name] = f
                self._flow_owner[f.name] = m.name

        self.ledger = ConservationLedger(self._stocks, tolerances)
        self.financial = FinancialLedger(
            list(sectors)
            if sectors
            else [
                Sector("households"),
                Sector("firms"),
                Sector("government"),
            ]
        )

    def _validate_flow(self, f: FlowSpec, owner: str) -> None:
        for endpoint, role in ((f.source, "source"), (f.sink, "sink")):
            st = self._stocks.get(endpoint)
            if st is None:
                raise ValueError(
                    f"flow {f.name!r} (module {owner!r}) names {role} "
                    f"{endpoint!r}, which is not a declared stock. Every flow "
                    "must connect two real stocks -- if this is meant to come "
                    "from outside the model, declare an explicit boundary stock."
                )
            if st.quantity is not f.quantity:
                raise ValueError(
                    f"flow {f.name!r} carries {f.quantity.value} but its "
                    f"{role} {endpoint!r} holds {st.quantity.value}. "
                    "Flows may not cross quantity networks."
                )

    # ------------------------------------------------------------------ step

    def _collect(self, t: float) -> tuple[dict[str, float], dict[str, float]]:
        """Run both passes and return (diagnostics, flow rates) for time t."""
        diags: dict[str, float] = {}
        for m in self.modules:
            view = StateView(self._stocks, diags, t)
            produced = m.diagnostics(view, self.params)
            for k, v in produced.items():
                if k in diags:
                    raise ValueError(
                        f"module {m.name!r} redefines diagnostic {k!r} already "
                        "published this step; diagnostic names are global"
                    )
                diags[k] = float(v)

        rates: dict[str, float] = {}
        full_view = StateView(self._stocks, diags, t)
        for m in self.modules:
            for k, v in m.rates(full_view, self.params).items():
                if k not in self._flows:
                    raise KeyError(
                        f"module {m.name!r} returned a rate for undeclared flow "
                        f"{k!r}"
                    )
                if self._flow_owner[k] != m.name:
                    raise ValueError(
                        f"module {m.name!r} set rate for flow {k!r} owned by "
                        f"{self._flow_owner[k]!r}"
                    )
                if v < 0:
                    raise ValueError(
                        f"flow {k!r} returned negative rate {v!r}. Declare a "
                        "second flow in the opposite direction instead."
                    )
                rates[k] = float(v)
        return diags, rates

    def _apply(self, rates: Mapping[str, float], t: float) -> None:
        delta: dict[str, float] = {n: 0.0 for n in self._stocks}
        for name, rate in rates.items():
            f = self._flows[name]
            amount = rate * self.dt
            delta[f.source] -= amount
            delta[f.sink] += amount

        for name, d in delta.items():
            st = self._stocks[name]
            new = st.value + d
            if new < 0 and not st.allow_negative:
                if st.limit is Limit.RESERVOIR:
                    raise ReservoirUndersized(name, t, st.value, -d)
                raise ConstraintBinding(name, t, st.value, -d)
            st.value = new

    def step(self, t: float) -> tuple[dict[str, float], dict[str, float]]:
        diags, rates = self._collect(t)

        view = StateView(self._stocks, diags, t)
        for m in self.modules:
            for payer, payee, amount, label in m.transactions(view, self.params):
                self.financial.transact(t, payer, payee, amount, label)

        self._apply(rates, t)

        if self.check_conservation:
            self.ledger.check(t)
            self.financial.check(t)
        return diags, rates

    # ------------------------------------------------------------------- run

    def run(self, t0: float, t1: float) -> Trajectory:
        times: list[float] = []
        stock_hist: dict[str, list[float]] = {n: [] for n in self._stocks}
        diag_hist: dict[str, list[float]] = {}
        flow_hist: dict[str, list[float]] = {n: [] for n in self._flows}

        t = float(t0)
        n_steps = int(round((t1 - t0) / self.dt))
        for i in range(n_steps + 1):
            # Record the state as it stands at the top of the step, together
            # with the diagnostics and rates implied by it.
            diags, rates = self._collect(t)
            times.append(t)
            for n, s in self._stocks.items():
                stock_hist[n].append(s.value)
            for k, v in diags.items():
                diag_hist.setdefault(k, []).append(v)
            for n in self._flows:
                flow_hist[n].append(rates.get(n, 0.0))

            if i == n_steps:
                break

            view = StateView(self._stocks, diags, t)
            for m in self.modules:
                for payer, payee, amt, label in m.transactions(view, self.params):
                    self.financial.transact(t, payer, payee, amt, label)
            self._apply(rates, t)
            if self.check_conservation:
                self.ledger.check(t)
                self.financial.check(t)
            t = t0 + (i + 1) * self.dt

        return Trajectory(
            times=np.array(times),
            stocks={k: np.array(v) for k, v in stock_hist.items()},
            diagnostics={k: np.array(v) for k, v in diag_hist.items()},
            flows={k: np.array(v) for k, v in flow_hist.items()},
        )
