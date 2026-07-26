"""L0 carbon cycle: four boxes, total carbon conserved.

Boxes: fossil reserves, atmosphere, ocean, biosphere. Emissions are a transfer
out of the reserve, so cumulative emissions can never exceed what is in the
ground -- the constraint that a "cumulative emissions" counter, the usual
implementation, cannot express.

Uptake form
-----------
Uptake is split into a fast term proportional to *current emissions* and a slow
term proportional to the *accumulated excess* over preindustrial:

    uptake = k_fast * emissions + k_slow * (C_atm - C_preindustrial)

The fast term looks like a fudge and is not. The airborne fraction has stayed
near 0.44 for seventy years while emissions grew fivefold, which a pure
excess-proportional box cannot reproduce: fitted to 1950 it under-predicts
present-day uptake by roughly a third. The reduced form above is what multi-box
impulse-response models (FaIR, and the Joos et al. response function) approximate
with a spectrum of timescales, and it is the smallest form that reproduces the
one fact the data actually pins down.

Its limitation is specific and worth stating: because the fast term is tied to
gross emissions, the model **cannot be trusted under net-negative emissions**.
Set emissions to zero and uptake collapses to the slow term alone. Any M5
scenario involving carbon removal needs the real impulse-response, not this.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..core.quantities import GTC_PER_PPM, GTCO2_PER_GTC, Quantity
from ..core.stocks import FlowSpec, StateView, Stock, StockKind
from .base import Module

#: Preindustrial atmospheric CO2, 278 ppm (IPCC AR6).
PREINDUSTRIAL_PPM = 278.0
PREINDUSTRIAL_GTC = PREINDUSTRIAL_PPM * GTC_PER_PPM


class Carbon(Module):
    name = "carbon"

    def __init__(
        self,
        t0: float,
        initial_ppm: float,
        fossil_reserves_gtc: float = 4000.0,
        ocean_gtc: float = 38000.0,
        biosphere_gtc: float = 2000.0,
    ) -> None:
        self.t0 = float(t0)
        self.initial_atmos_gtc = float(initial_ppm) * GTC_PER_PPM
        self.fossil_reserves_gtc = float(fossil_reserves_gtc)
        self.ocean_gtc = float(ocean_gtc)
        self.biosphere_gtc = float(biosphere_gtc)

    def stocks(self) -> list[Stock]:
        return [
            Stock(
                "atmosphere_c",
                Quantity.CARBON,
                self.initial_atmos_gtc,
                description="Atmospheric carbon, GtC.",
            ),
            Stock(
                "fossil_carbon_reserves",
                Quantity.CARBON,
                self.fossil_reserves_gtc,
                kind=StockKind.BOUNDARY,
                description="Carbon in recoverable fossil fuels, GtC.",
            ),
            Stock(
                "ocean_c",
                Quantity.CARBON,
                self.ocean_gtc,
                kind=StockKind.BOUNDARY,
                description="Ocean carbon, GtC.",
            ),
            Stock(
                "biosphere_c",
                Quantity.CARBON,
                self.biosphere_gtc,
                kind=StockKind.BOUNDARY,
                description="Land biosphere and soil carbon, GtC.",
            ),
        ]

    def flows(self) -> list[FlowSpec]:
        return [
            FlowSpec(
                "emissions",
                Quantity.CARBON,
                "fossil_carbon_reserves",
                "atmosphere_c",
            ),
            # Land-use change: carbon leaving the biosphere for the atmosphere.
            # Absent in M0, and its absence was diagnosable from the residuals:
            # concentration ran 4.5% low while emissions ran 30% high, which no
            # parameter error can produce. The uptake coefficient had been
            # calibrated against a carbon budget counting fossil *plus* land
            # use, while the model was fed fossil only, so roughly an eighth of
            # the real source term was simply missing.
            FlowSpec(
                "land_use_emissions",
                Quantity.CARBON,
                "biosphere_c",
                "atmosphere_c",
            ),
            FlowSpec("ocean_uptake", Quantity.CARBON, "atmosphere_c", "ocean_c"),
            FlowSpec(
                "biosphere_uptake", Quantity.CARBON, "atmosphere_c", "biosphere_c"
            ),
        ]

    def diagnostics(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        primary = view.diag("primary_energy_ej")

        # Carbon intensity is now an outcome of the low-carbon supply share,
        # which is itself an outcome of learning-curve cost and deployment
        # inertia. M0 had this as a fixed exponential decline, which is why an
        # emissions plateau was outside its reachable set at every parameter
        # value: a plateau needs intensity to fall faster than energy grows,
        # and a constant decline rate cannot accelerate.
        capacity = view.diag("lowcarbon_capacity")
        lowcarbon_share = min(capacity / primary, 1.0) if primary > 0 else 0.0
        ci = params["carbon_intensity_fossil"] * (1.0 - lowcarbon_share)
        fossil_gtc = primary * ci

        land_use_gtc = params["land_use_emissions_gtc"]
        total_gtc = fossil_gtc + land_use_gtc

        atmos = view.stock("atmosphere_c")
        excess = max(atmos - PREINDUSTRIAL_GTC, 0.0)
        uptake = params["uptake_fast"] * total_gtc + params["uptake_slow"] * excess
        uptake = min(uptake, excess)

        return {
            "co2_emissions_gtco2": fossil_gtc * GTCO2_PER_GTC,
            "emissions_gtc": fossil_gtc,
            "land_use_emissions_gtc_diag": land_use_gtc,
            "total_emissions_gtc": total_gtc,
            "lowcarbon_share": lowcarbon_share,
            "lowcarbon_share_pct": 100.0 * lowcarbon_share,
            "carbon_intensity_gtc_per_ej": ci,
            "co2_ppm": atmos / GTC_PER_PPM,
            "total_uptake_gtc": uptake,
            "airborne_fraction": (
                (total_gtc - uptake) / total_gtc if total_gtc > 0 else float("nan")
            ),
        }

    def rates(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        uptake = view.diag("total_uptake_gtc")
        ocean_share = params["ocean_uptake_share"]
        return {
            "emissions": view.diag("emissions_gtc"),
            "land_use_emissions": view.diag("land_use_emissions_gtc_diag"),
            "ocean_uptake": uptake * ocean_share,
            "biosphere_uptake": uptake * (1.0 - ocean_share),
        }
