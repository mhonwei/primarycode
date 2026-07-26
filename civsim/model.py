"""Assembly of the M1 single-region world model.

Module order is the no-simultaneity contract made concrete:

    population -> technology -> energy -> economy -> carbon

  population  reads capital and its own compartments; publishes labour,
              capital per head, age shares.
  technology  reads only its own knowledge stocks; publishes the multipliers
              every downstream module needs.
  energy      reads capital, labour, capital per head, efficiency multiplier;
              publishes primary energy and useful work.
  economy     reads labour, useful work, TFP multiplier; publishes output.
  carbon      reads primary energy and low-carbon capacity.

Technology sits second despite depending on output, because the dependency runs
through *rates*, not diagnostics: its multipliers come from stock levels known at
the top of the step, while R&D spending is set in pass 2 once output exists.
Nothing here is lagged a year to fake acyclicity. See modules/base.py.
"""

from __future__ import annotations

from typing import Any, Mapping

from .core.engine import Engine
from .core.financial import Sector
from .data.registry import Snapshot
from .modules.carbon import Carbon
from .modules.economy import Economy
from .modules.energy import Energy
from .modules.population import Population
from .modules.technology import Technology

#: Series the model produces that we hold against observation.
OBSERVED_SERIES = (
    "population_mn",
    "working_age_share_pct",
    "old_age_share_pct",
    "gdp_bn2011ppp",
    "primary_energy_ej",
    "lowcarbon_share_pct",
    "co2_emissions_gtco2",
    "co2_ppm",
)


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

    pop0 = ic["population_mn"] * 1e6
    working_share = ic["working_age_share_pct"] / 100.0
    old_share = ic["old_age_share_pct"] / 100.0
    y0 = ic["gdp_bn2011ppp"]
    e0 = ic["primary_energy_ej"]
    ppm0 = ic["co2_ppm"]

    k0 = y0 * params["capital_output_ratio"]
    labour0 = pop0 * working_share * params["participation_rate"]
    k_per_head0 = (k0 * 1e9) / pop0
    u0 = e0 * params["conv_eff_initial"]

    population = Population(
        initial_total=pop0,
        initial_working_share=working_share,
        initial_old_share=old_share,
    )
    technology = Technology(
        t0=t0,
        initial_lowcarbon_ej=e0 * params["initial_lowcarbon_share"],
    )
    energy = Energy(
        t0=t0,
        initial_capital=k0,
        initial_labour=labour0,
        initial_primary_energy=e0,
        initial_capital_per_head=k_per_head0,
    )
    economy = Economy(
        t0=t0,
        initial_output=y0,
        capital_output_ratio=params["capital_output_ratio"],
        initial_labour=labour0,
        initial_useful_work=u0,
    )
    carbon = Carbon(t0=t0, initial_ppm=ppm0)

    return Engine(
        modules=[population, technology, energy, economy, carbon],
        params=params,
        sectors=[
            Sector("households"),
            Sector("firms"),
            Sector("government"),
        ],
        dt=1.0,
        check_conservation=check_conservation,
    )
