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
        initial_capital_per_head: float,
        reserves_ej: float = 1.0e6,
    ) -> None:
        self.t0 = float(t0)
        self.initial_primary_energy = float(initial_primary_energy)
        self.reserves_ej = float(reserves_ej)
        self._kl0_cache: dict[float, float] = {}
        self._initial_capital = float(initial_capital)
        self._initial_labour = float(initial_labour)
        self._initial_capital_per_head = float(initial_capital_per_head)

    def _service_intensity(self, k_head: float, params: Mapping[str, Any]) -> float:
        """Energy service wanted per unit of capital, saturating in development.

        Normalised to 1.0 at t0 so it multiplies cleanly into the demand
        expression and carries no units of its own.
        """
        half = params["energy_service_half"]
        theta = params["energy_service_theta"]

        def raw(k: float) -> float:
            if k <= 0:
                return 0.0
            return 1.0 / (1.0 + (half / k) ** theta)

        base = raw(self._initial_capital_per_head)
        return raw(k_head) / base if base > 0 else 1.0

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
        # Energy per unit of K-L composite is now an *outcome* of accumulated
        # efficiency knowledge, not a fixed exponential in calendar time. This
        # is the change that makes decoupling reachable at all: M0's intensity
        # slope was fitted on 1950-1990 and nothing in the model could alter it,
        # so the post-1990 decoupling was structurally impossible to produce.
        # Energy demand needs two opposing mechanisms, not one.
        #
        # Efficiency knowledge only ever pushes intensity down, monotonically.
        # But observed energy per unit of K-L composite *rises* through
        # industrialisation and electrification and only falls later -- the
        # energy ladder, one of the stylised facts §11.8 requires the model to
        # reproduce rather than assume. A model with efficiency alone cannot
        # produce a turning point at any parameter value, which is the same
        # class of error as M0's fixed exponential, just better disguised.
        #
        # So: service demand per unit of capital rises with development and
        # saturates, while efficiency knowledge pulls the other way. The
        # observed hump is their crossing, and whether the model puts it in the
        # right decade is a test it can fail.
        k_head = view.diag("capital_per_head")
        service = self._service_intensity(k_head, params)
        primary = (
            self.initial_primary_energy
            * kl_n
            * service
            * view.diag("energy_intensity_multiplier")
        )

        # Conversion efficiency likewise tracks knowledge rather than the
        # calendar. It is kept separate from end-use intensity because they are
        # physically distinct -- thermodynamic conversion losses versus how much
        # service is wanted per unit of capital -- and collapsing them would
        # hide which of the two any future improvement came from.
        # The `max(..., 0)` is load-bearing, not defensive clutter. Knowledge can
        # fall below its t0 index when obsolescence outruns discovery, and
        # without the clamp the exponent flips sign, efficiency goes *negative*,
        # useful work goes negative, and the CES bracket returns a complex
        # number that propagates silently until something compares it to zero.
        # Conservation checks cannot catch this: nothing is created or
        # destroyed, the quantity is simply meaningless. Bounds on quantities
        # that have physical ranges have to be asserted separately.
        eff_inf = params["conv_eff_ceiling"]
        eff_0 = params["conv_eff_initial"]
        a_eff = view.diag("knowledge_efficiency_idx")
        eff = eff_inf - (eff_inf - eff_0) * math.exp(
            -params["conv_eff_rate"] * max(a_eff - 1.0, 0.0)
        )
        if not (0.0 < eff < 1.0):
            raise ValueError(
                f"conversion efficiency {eff:.4g} outside (0,1) at t={t:g}; "
                "a fraction of throughput cannot exceed unity or go negative"
            )

        return {
            "primary_energy_ej": primary,
            "energy_service_intensity": service,
            "conversion_efficiency": eff,
            "useful_exergy_efficiency_pct": 100.0 * eff,
            "useful_work_ej": primary * eff,
            "energy_per_kl": service * view.diag("energy_intensity_multiplier"),
        }

    def rates(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        return {"energy_extraction": view.diag("primary_energy_ej")}
