"""L2 economy: capital accumulation and KL-E production.

Production follows §9.1: energy enters as a factor, not as a cost share.

    inner = K^alpha * L^(1-alpha)
    Y     = Y0 * A(t) * [ beta * inner_n^rho + (1-beta) * U_n^rho ] ^ (1/rho)

with `inner_n` and `U_n` normalised to their t0 values so the bracket is
dimensionless, U the useful work delivered by the energy module, and
sigma = 1/(1-rho) the elasticity of substitution between the capital-labour
composite and useful work.

The substantive claim is sigma < 1: useful work and the K-L composite are
complements, not substitutes. Under the standard alternative -- energy as a
priced input with a ~6% cost share -- an energy supply shock can only ever have a
~6% effect on output, which is not what the 1970s look like. Low sigma is what
makes energy able to constrain output, and it is the parameter most worth
attacking if the backtest disappoints.

Capital is conserved as an accounting identity: investment is drawn from an
explicit source pool and depreciation is deposited in an explicit scrap pool, so
"investment appeared from nowhere" is a conservation failure rather than an
invisible assumption. The separate *economic* constraint -- that investment
cannot exceed output -- is not an accounting identity and is asserted directly.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

from ..core.quantities import Quantity
from ..core.stocks import FlowSpec, StateView, Stock, StockKind
from .base import Module


class InfeasibleAllocation(RuntimeError):
    """Investment plus consumption cannot exceed output."""


class Economy(Module):
    name = "economy"

    def __init__(
        self,
        t0: float,
        initial_output: float,
        capital_output_ratio: float,
        initial_labour: float,
        initial_useful_work: float,
        source_pool: float = 1.0e7,
    ) -> None:
        self.t0 = float(t0)
        self.initial_output = float(initial_output)
        self.initial_capital = float(initial_output) * float(capital_output_ratio)
        self.initial_labour = float(initial_labour)
        self.initial_useful_work = float(initial_useful_work)
        self.source_pool = float(source_pool)
        self._inner0: dict[float, float] = {}

    def inner0(self, alpha: float) -> float:
        if alpha not in self._inner0:
            self._inner0[alpha] = (
                self.initial_capital**alpha
                * self.initial_labour ** (1.0 - alpha)
            )
        return self._inner0[alpha]

    def stocks(self) -> list[Stock]:
        return [
            Stock(
                "capital",
                Quantity.CAPITAL,
                self.initial_capital,
                description="Productive capital stock, G$2011ppp.",
            ),
            Stock(
                "capital_source_pool",
                Quantity.CAPITAL,
                self.source_pool,
                kind=StockKind.BOUNDARY,
                description="Output not yet embodied as capital.",
            ),
            Stock(
                "scrapped_capital",
                Quantity.CAPITAL,
                0.0,
                kind=StockKind.BOUNDARY,
                description="Cumulative depreciation.",
            ),
        ]

    def flows(self) -> list[FlowSpec]:
        return [
            FlowSpec(
                "investment",
                Quantity.CAPITAL,
                "capital_source_pool",
                "capital",
            ),
            FlowSpec(
                "depreciation",
                Quantity.CAPITAL,
                "capital",
                "scrapped_capital",
            ),
        ]

    def diagnostics(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        t = view.t
        alpha = params["alpha"]
        rho = params["rho"]
        beta = params["beta"]

        k = view.stock("capital")
        lab = view.diag("labour")
        u = view.diag("useful_work_ej")

        inner_n = (k**alpha * lab ** (1.0 - alpha)) / self.inner0(alpha)
        u_n = u / self.initial_useful_work

        # TFP is now the productivity knowledge stock, not exp(g*t). The
        # difference matters beyond tidiness: a time trend keeps growing at the
        # fitted rate forever, whereas a knowledge stock drawn from a finite
        # frontier decelerates on its own. Which of those is right is an open
        # question; only one of them can be wrong in an informative way.
        tfp = view.diag("tfp_multiplier")
        bracket = beta * inner_n**rho + (1.0 - beta) * u_n**rho
        y = self.initial_output * tfp * bracket ** (1.0 / rho)

        investment = params["saving_rate"] * y
        rd = params["rd_share"] * y
        consumption = y - investment - rd
        if consumption < 0:
            raise InfeasibleAllocation(
                f"t={t:g}: investment {investment:.6g} plus R&D {rd:.6g} "
                f"exceeds output {y:.6g}. R&D competes with capital formation "
                "and consumption for the same output; it is not free."
            )

        pop = view.diag("population_mn") * 1e6
        return {
            "gdp_bn2011ppp": y,
            "gdp_per_capita": (y * 1e9) / pop,
            "tfp_index": tfp,
            "kl_composite_index": inner_n,
            "useful_work_index": u_n,
            "investment_bn": investment,
            "rd_bn": rd,
            "consumption_bn": consumption,
            "capital_output_ratio": k / y if y > 0 else float("nan"),
        }

    def rates(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        return {
            "investment": view.diag("investment_bn"),
            "depreciation": params["depreciation_rate"] * view.stock("capital"),
        }

    def transactions(
        self, view: StateView, params: Mapping[str, Any]
    ) -> list[tuple[str, str, float, str]]:
        """Minimal three-sector circuit.

        Not a serious closure -- it exists so the sum-to-zero invariant is
        exercised by real magnitudes from M0 onward, and so that adding a
        rest-of-world sector at M3 is a registration rather than a redesign.
        """
        y = view.diag("gdp_bn2011ppp")
        wages = params["labour_share"] * y
        tax = params["tax_rate"] * y
        saving = view.diag("investment_bn")
        return [
            ("firms", "households", wages, "wages"),
            ("firms", "government", tax, "tax"),
            ("government", "households", tax, "transfers"),
            ("households", "firms", saving, "investment_financing"),
        ]
