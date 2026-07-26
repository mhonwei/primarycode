"""World aggregation over regions.

Sums the regional modules' output into the world quantities the carbon module
and the technology module need, and publishes the regional *shares* that make
the cross-section scorable.

Why the shares are the point
----------------------------
M2 could not identify the two energy channels. The service ladder and the
efficiency knowledge stock both multiply into primary energy, and one world
aggregate cannot separate a demand curve from a technology trend: any pair that
fits 1950-1990 is admitted.

Two regions fix that, and not by adding parameters. The ladder is one *function*
shared by both regions -- so is the demographic transition -- and the regions
differ only in where they sit on it, because their capital per head differs by a
factor of five. The shape of the curve is then pinned by the contrast between
them at each date, while efficiency knowledge, being global, shifts both
together. That is the whole identification argument, and it costs one parameter
(a regional saving rate), not a parallel set.

A falsifiable side-effect
-------------------------
Technology here is global: one frontier, one deployment pool, one low-carbon
share applied to both regions. That forces `hi_co2_share_pct` to equal
`hi_energy_share_pct` exactly. Observation says otherwise -- 38% of energy but
33% of CO2 in 2020 -- because high-income regions deploy more low-carbon
capacity per unit of energy.

The series is scored anyway, and is expected to fail. The gap between the two
shares is a direct measurement of how much regional technology heterogeneity
matters, which is worth more than quietly omitting a prediction the model is
committed to making.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from ..core.stocks import StateView, Stock
from .base import Module


class WorldAggregate(Module):
    name = "aggregate"

    def __init__(self, regions: Sequence[str]) -> None:
        self.regions = list(regions)
        if not self.regions:
            raise ValueError("aggregate needs at least one region")

    def stocks(self) -> list[Stock]:
        return []

    def diagnostics(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        pop = {r: view.diag(f"{r}population_mn") for r in self.regions}
        gdp = {r: view.diag(f"{r}gdp_bn2011ppp") for r in self.regions}
        energy = {r: view.diag(f"{r}primary_energy_ej") for r in self.regions}
        useful = {r: view.diag(f"{r}useful_work_ej") for r in self.regions}
        working = {
            r: view.diag(f"{r}working_age_share_pct") * pop[r] / 100.0
            for r in self.regions
        }
        old = {
            r: view.diag(f"{r}old_age_share_pct") * pop[r] / 100.0
            for r in self.regions
        }

        pop_w = sum(pop.values())
        gdp_w = sum(gdp.values())
        energy_w = sum(energy.values())
        useful_w = sum(useful.values())

        out = {
            "population_mn": pop_w,
            "gdp_bn2011ppp": gdp_w,
            "primary_energy_ej": energy_w,
            "useful_work_ej": useful_w,
            "working_age_share_pct": 100.0 * sum(working.values()) / pop_w,
            "old_age_share_pct": 100.0 * sum(old.values()) / pop_w,
            # World conversion efficiency is the energy-weighted mean of the
            # regional efficiencies, not their average: a region using twice the
            # energy contributes twice as much to the world figure.
            "useful_exergy_efficiency_pct": 100.0 * useful_w / energy_w,
        }

        lead = self.regions[0]
        if len(self.regions) > 1:
            out["hi_pop_share_pct"] = 100.0 * pop[lead] / pop_w
            out["hi_gdp_share_pct"] = 100.0 * gdp[lead] / gdp_w
            out["hi_energy_share_pct"] = 100.0 * energy[lead] / energy_w
            # Equal to the energy share by construction, because technology is
            # global. Scored so that the assumption fails visibly rather than
            # silently. See the module docstring.
            out["hi_co2_share_pct"] = out["hi_energy_share_pct"]
        return out
