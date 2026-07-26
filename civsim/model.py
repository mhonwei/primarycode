"""Assembly of the M3 two-region world model.

Regions
-------
Two: `hi_` (high income) and `lo_` (rest of world). The split exists to identify
what one aggregate cannot -- see modules/aggregate.py for the argument.

**Almost every parameter stays global.** The energy service ladder and the
demographic transition are single functions of development, shared by both
regions; the regions differ only in where they sit on them, because their
capital per head differs by roughly a factor of five. That is what makes the
cross-section informative without enlarging the parameter budget (§11.6). Only
the saving rate is regional, because investment behaviour genuinely differs and
nothing else in the model can absorb that.

Module order
------------
    pop_hi, pop_lo -> technology -> energy_hi, energy_lo
                   -> econ_hi, econ_lo -> aggregate -> carbon

  pop_R        reads R capital; publishes R labour, capital per head, ages
  technology   reads only its own (global) knowledge stocks
  energy_R     reads R capital/labour/capital-per-head + global multipliers
  econ_R       reads R labour, R useful work, global TFP
  aggregate    sums regions; publishes world totals and regional shares
  carbon       reads world primary energy and global low-carbon capacity

Technology sits second despite depending on world output, because the dependency
runs through *rates*, not diagnostics: its multipliers come from stock levels
known at the top of the step, while R&D spending is set in pass 2 once output
exists. Nothing is lagged a year to fake acyclicity.
"""

from __future__ import annotations

from typing import Any, Mapping

from .core.engine import Engine
from .core.financial import Sector
from .data.registry import Snapshot
from .modules.aggregate import WorldAggregate
from .modules.carbon import Carbon
from .modules.economy import Economy
from .modules.energy import Energy
from .modules.population import Population
from .modules.technology import Technology

REGIONS = ("hi_", "lo_")

#: Series the model produces that we hold against observation.
OBSERVED_SERIES = (
    "population_mn",
    "working_age_share_pct",
    "old_age_share_pct",
    "gdp_bn2011ppp",
    "primary_energy_ej",
    "useful_exergy_efficiency_pct",
    "lowcarbon_share_pct",
    "co2_emissions_gtco2",
    "co2_ppm",
    # Cross-section. These are what the second region buys.
    "hi_pop_share_pct",
    "hi_gdp_share_pct",
    "hi_energy_share_pct",
    "hi_co2_share_pct",
)

#: World totals whose regional split is read from the snapshot.
_SPLIT = {
    "population_mn": "hi_pop_share_pct",
    "gdp_bn2011ppp": "hi_gdp_share_pct",
    "primary_energy_ej": "hi_energy_share_pct",
}


def initial_conditions(snapshot: Snapshot, t0: float) -> dict[str, float]:
    """Read t0 state straight from the snapshot, so it is never a free knob."""
    out = {}
    for name in OBSERVED_SERIES:
        s = snapshot.series(name)
        idx = list(s.years).index(t0)
        out[name] = float(s.values[idx])
    return out


def build_engine(
    params: Mapping[str, Any],
    snapshot: Snapshot,
    t0: float = 1950.0,
    check_conservation: bool = True,
) -> Engine:
    ic = initial_conditions(snapshot, t0)

    # Regional levels are reconstructed from world totals times the observed
    # share, so the regions sum to the world by construction rather than by
    # coincidence, and the world figure keeps its own (better) grade.
    split: dict[tuple[str, str], float] = {}
    for total, share_key in _SPLIT.items():
        hi_frac = ic[share_key] / 100.0
        split[("hi_", total)] = ic[total] * hi_frac
        split[("lo_", total)] = ic[total] * (1.0 - hi_frac)

    working_share = ic["working_age_share_pct"] / 100.0
    modules: list[Any] = []

    for r in REGIONS:
        modules.append(
            Population(
                initial_total=split[(r, "population_mn")] * 1e6,
                # Age structure is observed only at world level, so both regions
                # start from it. They diverge immediately because development
                # differs, which is the point of having two.
                initial_working_share=working_share,
                initial_old_share=ic["old_age_share_pct"] / 100.0,
                region=r,
            )
        )

    modules.append(
        Technology(
            t0=t0,
            initial_lowcarbon_ej=(
                ic["primary_energy_ej"] * params["initial_lowcarbon_share"]
            ),
            initial_modular_ej=(
                ic["primary_energy_ej"] * params["initial_modular_share"]
            ),
            regions=REGIONS,
        )
    )

    def regional_start(r: str) -> tuple[float, float, float, float]:
        pop0 = split[(r, "population_mn")] * 1e6
        y0 = split[(r, "gdp_bn2011ppp")]
        e0 = split[(r, "primary_energy_ej")]
        labour0 = pop0 * working_share * params["participation_rate"]
        return pop0, y0, e0, labour0

    for r in REGIONS:
        pop0, y0, e0, labour0 = regional_start(r)
        k0 = y0 * params["capital_output_ratio"]
        modules.append(
            Energy(
                t0=t0,
                initial_capital=k0,
                initial_labour=labour0,
                initial_primary_energy=e0,
                initial_capital_per_head=(k0 * 1e9) / pop0,
                region=r,
            )
        )

    for r in REGIONS:
        _, y0, e0, labour0 = regional_start(r)
        modules.append(
            Economy(
                t0=t0,
                initial_output=y0,
                capital_output_ratio=params["capital_output_ratio"],
                initial_labour=labour0,
                initial_useful_work=e0 * params["conv_eff_initial"],
                region=r,
            )
        )

    modules.append(WorldAggregate(regions=REGIONS))
    modules.append(Carbon(t0=t0, initial_ppm=ic["co2_ppm"]))

    return Engine(
        modules=modules,
        params=params,
        sectors=[
            Sector("households"),
            Sector("firms"),
            Sector("government"),
        ],
        dt=1.0,
        check_conservation=check_conservation,
    )
