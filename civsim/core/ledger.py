"""Conservation ledger: the check that makes the kernel worth having.

For each conserved quantity the ledger records the total across *all* stocks
(active and boundary) at build time, then re-checks it after every step. If
flows are paired correctly the total is invariant to floating-point roundoff.

This catches, mechanically and immediately:
  - a module writing a stock directly instead of declaring a flow
  - a flow whose source and sink are in different quantity networks
  - emissions that are not drawn from a reserve
  - investment that is not drawn from output

The last two are the ones that matter for the science. Most integrated
assessment models have no equivalent check, which is how "energy demand doubles
while fossil capacity retires" scenarios pass review: nothing in the model
object is obliged to notice that the material did not come from anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass

from .quantities import BASIS, DEFAULT_TOLERANCE, Quantity
from .stocks import Stock


class ConservationViolation(AssertionError):
    """Raised when a conserved quantity's total changes across a step."""


@dataclass(frozen=True)
class QuantityBalance:
    quantity: Quantity
    baseline: float
    current: float
    abs_error: float
    rel_error: float
    tolerance: float

    @property
    def ok(self) -> bool:
        return self.rel_error <= self.tolerance


class ConservationLedger:
    def __init__(
        self,
        stocks: dict[str, Stock],
        tolerances: dict[Quantity, float] | None = None,
    ) -> None:
        self._stocks = stocks
        self._tolerances = dict(DEFAULT_TOLERANCE)
        if tolerances:
            self._tolerances.update(tolerances)
        self._baseline: dict[Quantity, float] = self.totals()

    def totals(self) -> dict[Quantity, float]:
        out: dict[Quantity, float] = {}
        for s in self._stocks.values():
            out[s.quantity] = out.get(s.quantity, 0.0) + s.value
        return out

    def balances(self) -> list[QuantityBalance]:
        current = self.totals()
        res: list[QuantityBalance] = []
        for q, base in self._baseline.items():
            cur = current.get(q, 0.0)
            abs_err = abs(cur - base)
            # Scale by the baseline magnitude so tolerance means the same thing
            # for GtC (order 1e4) and persons (order 1e10).
            denom = max(abs(base), 1e-12)
            res.append(
                QuantityBalance(
                    quantity=q,
                    baseline=base,
                    current=cur,
                    abs_error=abs_err,
                    rel_error=abs_err / denom,
                    tolerance=self._tolerances[q],
                )
            )
        return res

    def check(self, t: float) -> None:
        bad = [b for b in self.balances() if not b.ok]
        if not bad:
            return
        lines = [f"conservation violated at t={t:g}:"]
        for b in bad:
            lines.append(
                f"  {b.quantity.value:8s} [{BASIS[b.quantity].value:10s}] "
                f"baseline={b.baseline:.10g} current={b.current:.10g} "
                f"rel_err={b.rel_error:.3e} > tol={b.tolerance:.1e}"
            )
        lines.append(
            "A quantity total changed. Either a module mutated a stock directly "
            "instead of declaring a flow, or a flow is unpaired. Both are bugs "
            "in the model, not in the check."
        )
        raise ConservationViolation("\n".join(lines))
