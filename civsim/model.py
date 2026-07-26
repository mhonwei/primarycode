"""Assembly of the M0 single-region world model.

Module order is the no-simultaneity contract made concrete:

    population -> energy -> economy -> carbon

  population  reads capital (a stock) and its own stock; publishes labour.
  energy      reads capital and labour; publishes primary energy, useful work.
  economy     reads labour and useful work; publishes output, investment.
  carbon      reads primary energy; publishes emissions and ppm.

Nothing in this chain reads a value produced later in the same step, and nothing
is lagged a year to pretend the loop is broken. The one place a genuine
simultaneity was cut -- energy demand driven by installed capital and labour
rather than by contemporaneous output -- is argued in modules/energy.py rather
than hidden here.
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

#: Series the M0 model produces that we hold against observation.
OBSERVED_SERIES = (
    "population_mn",
    "gdp_bn2011ppp",
    "primary_energy_ej",
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
    y0 = ic["gdp_bn2011ppp"]
    e0 = ic["primary_energy_ej"]
    ppm0 = ic["co2_ppm"]

    k0 = y0 * params["capital_output_ratio"]
    labour0 = pop0 * params["participation_rate"]
    # Useful work at t0 uses the initial conversion efficiency by construction,
    # so the economy's normalisation and the energy module's output agree at t0.
    u0 = e0 * params["conv_eff_initial"]

    population = Population(initial_population=pop0)
    energy = Energy(
        t0=t0,
        initial_capital=k0,
        initial_labour=labour0,
        initial_primary_energy=e0,
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
        modules=[population, energy, economy, carbon],
        params=params,
        sectors=[
            Sector("households"),
            Sector("firms"),
            Sector("government"),
        ],
        dt=1.0,
        check_conservation=check_conservation,
    )
