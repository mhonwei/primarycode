"""L2 energy: extraction, conversion, and useful work.

Two things here matter for the design and are worth stating plainly.

**Energy is conserved, and the model says where it goes.** Primary energy is a
transfer out of a finite reserve and, within the year, ends up as dissipated
heat. Useful work is a *fraction of that throughput*, not a stock -- there is no
box where usable energy accumulates. This is why `energy_extraction` runs
reserves -> dissipated_heat and the conservation check has real content: any
attempt to supply energy the reserve does not contain shows up as a negative
stock, not as a quietly larger number.

**Demand is driven by installed capital and labour, not by output.** The
conventional formulation is E = intensity x GDP, which cannot be evaluated
before GDP exists and so forces either a lag or a fixed-point solve. Driving
demand off the K-L composite already in place at the start of the step removes
the simultaneity outright, and is the more physical statement anyway: energy is
consumed by the stock of energy-using equipment and the people operating it, not
by an accounting aggregate computed at year end.

Useful work (exergy services actually delivered) rather than primary energy is
what enters production, following Ayres & Warr. The aggregate conversion
efficiency of the world energy system is order 10% and has roughly doubled over
the twentieth century; treating that improvement as part of the growth process,
instead of folding it into an unexplained TFP residual, is the point of §9.1.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

from ..core.quantities import Quantity
from ..core.stocks import FlowSpec, StateView, Stock, StockKind
from .base import Module


class Energy(Module):
    name = "energy"

    def __init__(
        self,
        t0: float,
        initial_capital: float,
        initial_labour: float,
        initial_primary_energy: float,
        reserves_ej: float = 1.0e6,
    ) -> None:
        self.t0 = float(t0)
        self.initial_primary_energy = float(initial_primary_energy)
        self.reserves_ej = float(reserves_ej)
        self._kl0_cache: dict[float, float] = {}
        self._initial_capital = float(initial_capital)
        self._initial_labour = float(initial_labour)

    def kl0(self, alpha: float) -> float:
        """K-L composite at t0, cached per alpha (used for normalisation)."""
        if alpha not in self._kl0_cache:
            self._kl0_cache[alpha] = (
                self._initial_capital**alpha
                * self._initial_labour ** (1.0 - alpha)
            )
        return self._kl0_cache[alpha]

    def stocks(self) -> list[Stock]:
        return [
            Stock(
                "energy_reserves",
                Quantity.ENERGY,
                self.reserves_ej,
                kind=StockKind.BOUNDARY,
                description=(
                    "Recoverable primary energy, EJ. Set large in M0 so it does "
                    "not bind; making depletion bite is M2 work."
                ),
            ),
            Stock(
                "dissipated_heat",
                Quantity.ENERGY,
                0.0,
                kind=StockKind.BOUNDARY,
                description="Cumulative energy degraded to low-grade heat, EJ.",
            ),
        ]

    def flows(self) -> list[FlowSpec]:
        return [
            FlowSpec(
                "energy_extraction",
                Quantity.ENERGY,
                "energy_reserves",
                "dissipated_heat",
                description=(
                    "Primary energy withdrawn and, within the year, dissipated."
                ),
            )
        ]

    def diagnostics(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        t = view.t
        alpha = params["alpha"]
        kl = view.stock("capital") ** alpha * view.diag("labour") ** (1.0 - alpha)
        kl_n = kl / self.kl0(alpha)

        # Autonomous change in energy required per unit of K-L composite.
        eps = params["energy_per_kl_growth"]
        primary = self.initial_primary_energy * kl_n * math.exp(eps * (t - self.t0))

        eff_inf = params["conv_eff_ceiling"]
        eff_0 = params["conv_eff_initial"]
        g = params["conv_eff_rate"]
        eff = eff_inf - (eff_inf - eff_0) * math.exp(-g * (t - self.t0))

        return {
            "primary_energy_ej": primary,
            "conversion_efficiency": eff,
            "useful_work_ej": primary * eff,
        }

    def rates(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        return {"energy_extraction": view.diag("primary_energy_ej")}
