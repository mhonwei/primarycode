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
from ..core.stocks import FlowSpec, Limit, StateView, Stock, StockKind
from .base import Module


class InfeasibleAllocation(RuntimeError):
    """Investment plus consumption cannot exceed output."""


class Economy(Module):
    def __init__(
        self,
        t0: float,
        initial_output: float,
        capital_output_ratio: float,
        initial_labour: float,
        initial_useful_work: float,
        source_pool: float = 1.0e12,
        region: str = "",
    ) -> None:
        self.region = region
        self.name = f"economy_{region or 'world'}"
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
                f"{self.region}capital",
                Quantity.CAPITAL,
                self.initial_capital,
                description="Productive capital stock, G$2011ppp.",
            ),
            Stock(
                f"{self.region}capital_source_pool",
                Quantity.CAPITAL,
                self.source_pool,
                kind=StockKind.BOUNDARY,
                limit=Limit.RESERVOIR,
                description="Output not yet embodied as capital.",
            ),
            Stock(
                f"{self.region}scrapped_capital",
                Quantity.CAPITAL,
                0.0,
                kind=StockKind.BOUNDARY,
                limit=Limit.RESERVOIR,
                description="Cumulative depreciation.",
            ),
        ]

    def flows(self) -> list[FlowSpec]:
        return [
            FlowSpec(
                f"{self.region}investment",
                Quantity.CAPITAL,
                f"{self.region}capital_source_pool",
                f"{self.region}capital",
            ),
            FlowSpec(
                f"{self.region}depreciation",
                Quantity.CAPITAL,
                f"{self.region}capital",
                f"{self.region}scrapped_capital",
            ),
        ]

    def diagnostics(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        t = view.t
        alpha = params["alpha"]
        rho = params["rho"]
        beta = params["beta"]

        R = self.region
        k = view.stock(f"{R}capital")
        lab = view.diag(f"{R}labour")
        u = view.diag(f"{R}useful_work_ej")

        inner_n = (k**alpha * lab ** (1.0 - alpha)) / self.inner0(alpha)
        u_n = u / self.initial_useful_work

        # TFP is now the productivity knowledge stock, not exp(g*t). The
        # difference matters beyond tidiness: a time trend keeps growing at the
        # fitted rate forever, whereas a knowledge stock drawn from a finite
        # frontier decelerates on its own. Which of those is right is an open
        # question; only one of them can be wrong in an informative way.
        tfp = view.diag(f"tfp_multiplier_{R}")
        bracket = beta * inner_n**rho + (1.0 - beta) * u_n**rho
        y = self.initial_output * tfp * bracket ** (1.0 / rho)

        investment = params[f"saving_rate_{R or 'world'}"] * y
        rd = params["rd_share"] * y
        consumption = y - investment - rd
        if consumption < 0:
            raise InfeasibleAllocation(
                f"t={t:g}: investment {investment:.6g} plus R&D {rd:.6g} "
                f"exceeds output {y:.6g}. R&D competes with capital formation "
                "and consumption for the same output; it is not free."
            )

        pop = view.diag(f"{R}population_mn") * 1e6
        return {
            f"{R}gdp_bn2011ppp": y,
            f"{R}gdp_per_capita": (y * 1e9) / pop,
            f"{R}tfp_index": tfp,
            f"{R}kl_composite_index": inner_n,
            f"{R}useful_work_index": u_n,
            f"{R}investment_bn": investment,
            f"{R}rd_bn": rd,
            f"{R}consumption_bn": consumption,
            f"{R}capital_output_ratio": k / y if y > 0 else float("nan"),
        }

    def rates(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        R = self.region
        return {
            f"{R}investment": view.diag(f"{R}investment_bn"),
            f"{R}depreciation": (
                params["depreciation_rate"] * view.stock(f"{R}capital")
            ),
        }

    def transactions(
        self, view: StateView, params: Mapping[str, Any]
    ) -> list[tuple[str, str, float, str]]:
        """Minimal three-sector circuit.

        Not a serious closure -- it exists so the sum-to-zero invariant is
        exercised by real magnitudes from M0 onward, and so that adding a
        rest-of-world sector at M3 is a registration rather than a redesign.
        """
        R = self.region
        y = view.diag(f"{R}gdp_bn2011ppp")
        wages = params["labour_share"] * y
        tax = params["tax_rate"] * y
        saving = view.diag(f"{R}investment_bn")
        return [
            ("firms", "households", wages, f"{R}wages"),
            ("firms", "government", tax, f"{R}tax"),
            ("government", "households", tax, f"{R}transfers"),
            ("households", "firms", saving, f"{R}investment_financing"),
        ]
