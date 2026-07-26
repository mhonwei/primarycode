"""L1 population, M0 form: aggregate stock with income-driven vital rates.

This is deliberately *not* the cohort-component model. Cohorts are M1 work, and
building them here would mean calibrating age-specific rates against a 5-yearly
aggregate snapshot -- fitting more parameters than the data can identify, which
is the §2.1 failure mode the whole project is trying to avoid.

What M0 does keep is the mechanism that carries the demographic transition:
crude birth and death rates fall along a saturating curve in development level.
Development is proxied by **capital per head**, not by output per head. That
choice is forced by the no-simultaneity rule -- output is computed later in the
same step -- but it is also defensible on its own terms: the transition responds
to accumulated conditions (infrastructure, schooling, urban form) rather than to
the current year's flow of income, and K/N is monotone in Y/N here anyway.

Known limitation, to be removed at M1: the crude death rate is monotone
decreasing in development. Real CDR turns back up as populations age, which is
precisely the dynamic that dominates China, Japan, Korea and Europe over the
horizon this project cares about. M0 therefore *understates* deaths late in the
run, and its population path should be read as an upper envelope.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..core.quantities import Quantity
from ..core.stocks import FlowSpec, StateView, Stock, StockKind
from .base import Module


def _saturating(x: float, lo: float, hi: float, half: float, theta: float) -> float:
    """Rate falling from `hi` to `lo` as x rises through `half`."""
    if x <= 0:
        return hi
    return lo + (hi - lo) / (1.0 + (x / half) ** theta)


class Population(Module):
    name = "population"

    def __init__(self, initial_population: float) -> None:
        self.initial_population = float(initial_population)

    def stocks(self) -> list[Stock]:
        return [
            Stock(
                "population",
                Quantity.PERSONS,
                self.initial_population,
                description="World population, persons.",
            ),
            Stock(
                "unborn_pool",
                Quantity.PERSONS,
                1e11,
                kind=StockKind.BOUNDARY,
                description=(
                    "Reservoir births are drawn from. Exists so that births are "
                    "a transfer rather than an appearance -- see core/stocks.py."
                ),
            ),
            Stock(
                "deceased_pool",
                Quantity.PERSONS,
                0.0,
                kind=StockKind.BOUNDARY,
                description="Cumulative deaths.",
            ),
        ]

    def flows(self) -> list[FlowSpec]:
        return [
            FlowSpec("births", Quantity.PERSONS, "unborn_pool", "population"),
            FlowSpec("deaths", Quantity.PERSONS, "population", "deceased_pool"),
        ]

    def diagnostics(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        n = view.stock("population")
        k = view.stock("capital")  # G$2011ppp
        # Capital per head in dollars: K is in billions.
        k_per_head = (k * 1e9) / n if n > 0 else 0.0

        cbr = _saturating(
            k_per_head,
            params["cbr_min"],
            params["cbr_max"],
            params["cbr_half"],
            params["cbr_theta"],
        )
        cdr = _saturating(
            k_per_head,
            params["cdr_min"],
            params["cdr_max"],
            params["cdr_half"],
            params["cdr_theta"],
        )
        return {
            "population_mn": n / 1e6,
            "capital_per_head": k_per_head,
            "crude_birth_rate": cbr,
            "crude_death_rate": cdr,
            # Labour supply. The participation rate is constant in M0, so it
            # cancels out of every normalised ratio; it is kept explicit so that
            # M1 can replace it with a working-age share without changing the
            # production function's interface.
            "labour": n * params["participation_rate"],
        }

    def rates(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        n = view.stock("population")
        return {
            "births": n * view.diag("crude_birth_rate") / 1000.0,
            "deaths": n * view.diag("crude_death_rate") / 1000.0,
        }
