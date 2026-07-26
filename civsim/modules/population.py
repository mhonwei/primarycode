"""L1 population: age compartments with Erlang-staged transit.

M0 carried one aggregate population stock with a crude death rate falling
monotonically in development. Its documented flaw was that ageing could never
turn mortality back up -- the single dynamic that dominates the countries this
project most needs to say something about.

Why stages, not compartments
----------------------------
The obvious fix is three compartments (0-14, 15-64, 65+) with transit rates
1/15 and 1/50. That was tried and fails, for a reason worth recording because it
is invisible until you check the age structure against data.

A single compartment has an *exponential* dwell time: memoryless, with a long
tail. It therefore behaves as though the 15-64 population were uniformly spread
across those fifty years. In a rapidly growing population it is not -- it is
heavily weighted toward the young end, so far fewer than 1/50 of it turns 65 in
any given year. The three-compartment model consequently produced a 65+ share of
7-19% at 1990 against 6.2% observed: the observation fell *outside* the entire
prior predictive range.

The linear chain trick fixes this with no new free parameters. Splitting a
compartment into k sequential stages turns the dwell time from exponential into
Erlang-k, which concentrates around the intended transit time instead of
spreading over it. Each stage passes at rate k/width -- still arithmetic, still
not fitted. The later stages are small in a growing population, which is exactly
the demographic fact the single compartment could not represent.

This is the kind of structure that should come from arithmetic rather than from
calibration (§11.6): it adds realism the data cannot identify but geometry can.

Still deferred to M2
--------------------
Single-year cohorts, and with them age-specific fertility and mortality
schedules. Those need roughly forty more parameters against nine 5-yearly
aggregate observations -- the §2.1 failure mode. They arrive when national age
distributions do.

What this buys: the working-age share becomes a scored *output*. Its observed
path is not monotone -- it falls to ~57% around 1970 as the post-war cohorts are
still children, then rises to a ~65.5% peak around 2012. A model without age
structure cannot produce a turning point at all, so this is a structural test in
the sense of §11.8, not a fitting target.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

from ..core.quantities import Quantity
from ..core.stocks import FlowSpec, StateView, Stock, StockKind
from .base import Module

#: Compartment widths in years, and the number of Erlang stages each is split
#: into. Transit rate per stage is stages/width -- arithmetic, never fitted.
YOUTH_YEARS, YOUTH_STAGES = 15.0, 3
WORKING_YEARS, WORKING_STAGES = 50.0, 5

#: Growth rate used to spread the initial population across stages. A growing
#: population has more people in early stages; assuming a flat split would put
#: the model in a transient it never recovers from.
INITIAL_GROWTH_RATE = 0.018


def _saturating(x: float, lo: float, hi: float, half: float, theta: float) -> float:
    """Rate falling from `hi` to `lo` as x rises through `half`."""
    if x <= 0:
        return hi
    return lo + (hi - lo) / (1.0 + (x / half) ** theta)


def _stage_weights(width: float, stages: int, start_age: float) -> list[float]:
    """Stable-age-distribution weights across the stages of a compartment."""
    step = width / stages
    w = [
        math.exp(-INITIAL_GROWTH_RATE * (start_age + (i + 0.5) * step))
        for i in range(stages)
    ]
    total = sum(w)
    return [x / total for x in w]


class Population(Module):
    name = "population"

    def __init__(
        self,
        initial_total: float,
        initial_working_share: float,
        initial_old_share: float,
    ) -> None:
        total = float(initial_total)
        self.initial_total = total
        working = total * float(initial_working_share)
        old = total * float(initial_old_share)
        youth = total - working - old
        if youth <= 0:
            raise ValueError(
                "initial youth compartment is non-positive; working and old "
                "shares sum above 1"
            )
        self.initial_youth_stages = [
            youth * w for w in _stage_weights(YOUTH_YEARS, YOUTH_STAGES, 0.0)
        ]
        self.initial_working_stages = [
            working * w
            for w in _stage_weights(WORKING_YEARS, WORKING_STAGES, YOUTH_YEARS)
        ]
        self.initial_old = old

    # ------------------------------------------------------------- naming

    @staticmethod
    def youth(i: int) -> str:
        return f"pop_youth_{i}"

    @staticmethod
    def working(i: int) -> str:
        return f"pop_working_{i}"

    # ------------------------------------------------------------- stocks

    def stocks(self) -> list[Stock]:
        out: list[Stock] = []
        for i, v in enumerate(self.initial_youth_stages):
            lo = i * YOUTH_YEARS / YOUTH_STAGES
            hi = (i + 1) * YOUTH_YEARS / YOUTH_STAGES
            out.append(
                Stock(self.youth(i), Quantity.PERSONS, v,
                      description=f"Population aged {lo:.0f}-{hi:.0f}.")
            )
        for i, v in enumerate(self.initial_working_stages):
            lo = YOUTH_YEARS + i * WORKING_YEARS / WORKING_STAGES
            hi = YOUTH_YEARS + (i + 1) * WORKING_YEARS / WORKING_STAGES
            out.append(
                Stock(self.working(i), Quantity.PERSONS, v,
                      description=f"Population aged {lo:.0f}-{hi:.0f}.")
            )
        out.append(
            Stock("pop_old", Quantity.PERSONS, self.initial_old,
                  description="Population aged 65+.")
        )
        out.append(
            Stock("unborn_pool", Quantity.PERSONS, 1e11, kind=StockKind.BOUNDARY,
                  description="Reservoir births are drawn from.")
        )
        out.append(
            Stock("deceased_pool", Quantity.PERSONS, 0.0, kind=StockKind.BOUNDARY,
                  description="Cumulative deaths.")
        )
        return out

    def flows(self) -> list[FlowSpec]:
        P = Quantity.PERSONS
        out = [FlowSpec("births", P, "unborn_pool", self.youth(0))]
        for i in range(YOUTH_STAGES - 1):
            out.append(
                FlowSpec(f"age_youth_{i}", P, self.youth(i), self.youth(i + 1))
            )
        out.append(
            FlowSpec("maturing", P, self.youth(YOUTH_STAGES - 1), self.working(0))
        )
        for i in range(WORKING_STAGES - 1):
            out.append(
                FlowSpec(
                    f"age_working_{i}", P, self.working(i), self.working(i + 1)
                )
            )
        out.append(
            FlowSpec("retiring", P, self.working(WORKING_STAGES - 1), "pop_old")
        )
        for i in range(YOUTH_STAGES):
            out.append(
                FlowSpec(f"deaths_youth_{i}", P, self.youth(i), "deceased_pool")
            )
        for i in range(WORKING_STAGES):
            out.append(
                FlowSpec(f"deaths_working_{i}", P, self.working(i), "deceased_pool")
            )
        out.append(FlowSpec("deaths_old", P, "pop_old", "deceased_pool"))
        return out

    # -------------------------------------------------------- diagnostics

    def diagnostics(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        youth = sum(view.stock(self.youth(i)) for i in range(YOUTH_STAGES))
        working = sum(view.stock(self.working(i)) for i in range(WORKING_STAGES))
        old = view.stock("pop_old")
        total = youth + working + old

        k = view.stock("capital")
        k_per_head = (k * 1e9) / total if total > 0 else 0.0

        fert = _saturating(
            k_per_head, params["fert_min"], params["fert_max"],
            params["fert_half"], params["fert_theta"],
        )
        # One development-driven mortality scale, three compartment ratios. The
        # aggregate crude death rate then rises whenever the old compartment
        # grows relative to the rest, without anything being told to make it
        # rise -- which is the mechanism M0 structurally lacked.
        scale = _saturating(
            k_per_head, params["mort_min"], params["mort_max"],
            params["mort_half"], params["mort_theta"],
        )
        m_youth = scale * params["mort_ratio_youth"]
        m_working = scale * params["mort_ratio_working"]
        m_old = scale * params["mort_ratio_old"]

        deaths = (youth * m_youth + working * m_working + old * m_old) / 1000.0

        return {
            "population_mn": total / 1e6,
            "working_age_share_pct": 100.0 * working / total,
            "old_age_share_pct": 100.0 * old / total,
            "youth_share_pct": 100.0 * youth / total,
            "capital_per_head": k_per_head,
            "fertility_rate": fert,
            "mortality_scale": scale,
            "crude_death_rate": 1000.0 * deaths / total,
            "crude_birth_rate": working * fert / total,
            "old_age_dependency": old / working if working > 0 else float("nan"),
            # Labour now tracks the working-age compartment, so the demographic
            # transition reaches production through a channel that exists.
            "labour": working * params["participation_rate"],
            "_m_youth": m_youth,
            "_m_working": m_working,
            "_m_old": m_old,
        }

    # --------------------------------------------------------------- rates

    def rates(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        working_total = sum(
            view.stock(self.working(i)) for i in range(WORKING_STAGES)
        )
        youth_rate = YOUTH_STAGES / YOUTH_YEARS
        working_rate = WORKING_STAGES / WORKING_YEARS
        m_y = view.diag("_m_youth") / 1000.0
        m_w = view.diag("_m_working") / 1000.0

        out: dict[str, float] = {
            "births": working_total * view.diag("fertility_rate") / 1000.0,
            "deaths_old": view.stock("pop_old") * view.diag("_m_old") / 1000.0,
        }
        for i in range(YOUTH_STAGES):
            v = view.stock(self.youth(i))
            out[f"deaths_youth_{i}"] = v * m_y
            if i < YOUTH_STAGES - 1:
                out[f"age_youth_{i}"] = v * youth_rate
            else:
                out["maturing"] = v * youth_rate
        for i in range(WORKING_STAGES):
            v = view.stock(self.working(i))
            out[f"deaths_working_{i}"] = v * m_w
            if i < WORKING_STAGES - 1:
                out[f"age_working_{i}"] = v * working_rate
            else:
                out["retiring"] = v * working_rate
        return out
