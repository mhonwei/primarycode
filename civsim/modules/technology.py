"""L3 technology: knowledge stocks, learning curves, diffusion.

Why this module exists
----------------------
M0 had no technology layer. It had two exponentials -- energy intensity falling
at a fixed rate, carbon intensity falling at a fixed rate -- and a third for TFP.
Two of M0's three structural failures were direct consequences:

  * energy demand could not decouple, because intensity decline was a constant
    fitted on 1950-1990 and nothing could change its slope;
  * emissions could not plateau, because a plateau requires carbon intensity to
    fall *faster* than energy grows, which a fixed exponential cannot do.

A fixed exponential is not a model of technology. It is a model of *the absence*
of technology as a process, with the observed consequence of technology pasted
on. Replacing it is the whole of M1.

What is modelled
----------------
Three knowledge stocks, each an index normalised to 1.0 at t0:

  productivity   general-purpose knowledge -> total factor productivity
  efficiency     energy-efficiency knowledge -> energy per unit of K-L composite
  lowcarbon      low-carbon energy knowledge -> deployment cost, hence share

Each accumulates by semi-endogenous R&D (Jones 1995):

    dA/dt = lambda * R^phi * A^psi * (F/F0)^xi  -  delta_A * A

  R      R&D spending in the domain, a share of output
  phi<1  duplication: two labs on one problem are worth less than two problems
  psi<1  standing on shoulders, with diminishing returns
  F      remaining frontier pool
  xi>0   fishing out: ideas get harder to find as the pool is drawn down

Semi-endogenous rather than fully endogenous is a deliberate choice, and the
same one design §16.3 makes about AI. Fully endogenous growth has scale effects:
more researchers give a permanently higher growth rate, and once you couple that
to output the model produces a singularity somewhere in the next century. That
is a property of the functional form, not a finding about the world, and a model
whose headline result is manufactured by its own growth equation is worthless.
The frontier pool makes the deceleration structural rather than a fitted damper.

Deployment learning is separate from research, and is where the plateau
mechanism lives. Low-carbon unit cost follows Wright's law in cumulative
deployment, and the deployed share follows a logistic driven by the cost ratio
against fossil. Neither R&D alone nor learning alone produces a transition:
research lowers the intercept, deployment lowers the cost along the way, and the
share moves only when cost parity is approached. That interaction is why a
plateau is now inside the model's reachable set -- not because a parameter was
added that permits one.

Conservation
------------
Knowledge is conserved by accounting convention (see core/quantities.py). Each
domain draws discovery from a finite `frontier_pool_*` and sheds obsolescence
into `obsolete_*`. The convention is not decoration: the depleting pool *is* the
fishing-out term, so the bookkeeping and the economics are the same object.

Ordering
--------
The multipliers this module publishes depend only on stock levels, so they are
available in diagnostics pass 1 to every module downstream. R&D spending depends
on output, which is computed later in the same step -- and that is fine, because
rates are computed in pass 2 once the full diagnostic context exists. No lag, no
fixed-point solve. See modules/base.py for the contract.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

from ..core.quantities import Quantity
from ..core.stocks import FlowSpec, StateView, Stock, StockKind
from .base import Module

DOMAINS = ("productivity", "efficiency", "lowcarbon")


class Technology(Module):
    name = "technology"

    def __init__(
        self,
        t0: float,
        initial_lowcarbon_ej: float,
        frontier_pool: float = 40.0,
    ) -> None:
        self.t0 = float(t0)
        self.initial_lowcarbon_ej = float(initial_lowcarbon_ej)
        self.frontier_pool = float(frontier_pool)

    # ------------------------------------------------------------- stocks

    def stocks(self) -> list[Stock]:
        out: list[Stock] = []
        for d in DOMAINS:
            out.append(
                Stock(
                    f"knowledge_{d}",
                    Quantity.KNOWLEDGE,
                    1.0,
                    description=f"{d} knowledge index, 1.0 at t0.",
                )
            )
            out.append(
                Stock(
                    f"frontier_pool_{d}",
                    Quantity.KNOWLEDGE,
                    self.frontier_pool,
                    kind=StockKind.BOUNDARY,
                    description=(
                        f"Undiscovered {d} knowledge. Depletion is the "
                        "fishing-out effect, not bookkeeping."
                    ),
                )
            )
            out.append(
                Stock(
                    f"obsolete_{d}",
                    Quantity.KNOWLEDGE,
                    0.0,
                    kind=StockKind.BOUNDARY,
                    description=f"Retired {d} knowledge.",
                )
            )
        # Low-carbon capacity, in EJ/yr of primary-equivalent supply.
        #
        # Two quantities are needed and they are not the same: the learning
        # curve runs on *cumulative* deployment (experience is never unlearned)
        # while the supply share runs on *current* capacity (plant retires).
        # Keeping capacity and retirement as separate stocks gives both --
        # cumulative is their sum -- without a counter that the conservation
        # ledger cannot see.
        out.append(
            Stock(
                "lowcarbon_capacity_ej",
                Quantity.ENERGY,
                self.initial_lowcarbon_ej,
                kind=StockKind.BOUNDARY,
                description="Operating low-carbon supply, EJ/yr.",
            )
        )
        out.append(
            Stock(
                "lowcarbon_retired_ej",
                Quantity.ENERGY,
                0.0,
                kind=StockKind.BOUNDARY,
                description="Retired low-carbon capacity, EJ/yr equivalent.",
            )
        )
        out.append(
            Stock(
                "deployment_pool",
                Quantity.ENERGY,
                1.0e7,
                kind=StockKind.BOUNDARY,
                description="Source pool for deployment accounting.",
            )
        )
        return out

    def flows(self) -> list[FlowSpec]:
        out: list[FlowSpec] = []
        for d in DOMAINS:
            out.append(
                FlowSpec(
                    f"discovery_{d}",
                    Quantity.KNOWLEDGE,
                    f"frontier_pool_{d}",
                    f"knowledge_{d}",
                )
            )
            out.append(
                FlowSpec(
                    f"obsolescence_{d}",
                    Quantity.KNOWLEDGE,
                    f"knowledge_{d}",
                    f"obsolete_{d}",
                )
            )
        out.append(
            FlowSpec(
                "lowcarbon_deployment",
                Quantity.ENERGY,
                "deployment_pool",
                "lowcarbon_capacity_ej",
            )
        )
        out.append(
            FlowSpec(
                "lowcarbon_retirement",
                Quantity.ENERGY,
                "lowcarbon_capacity_ej",
                "lowcarbon_retired_ej",
            )
        )
        return out

    # -------------------------------------------------------- diagnostics

    def diagnostics(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        a_prod = view.stock("knowledge_productivity")
        a_eff = view.stock("knowledge_efficiency")
        a_low = view.stock("knowledge_lowcarbon")
        capacity = view.stock("lowcarbon_capacity_ej")
        cumulative = capacity + view.stock("lowcarbon_retired_ej")

        # --- Wright learning curve on cumulative low-carbon deployment ----
        # Cost falls by `learning_rate` per doubling of cumulative experience;
        # research shifts the intercept down separately. Experience is never
        # unlearned, which is why this runs on cumulative rather than capacity.
        b = -math.log(1.0 - params["learning_rate"]) / math.log(2.0)
        cost_lowcarbon = (
            params["lowcarbon_cost_0"]
            * (cumulative / self.initial_lowcarbon_ej) ** (-b)
            * a_low ** (-params["rnd_cost_elasticity"])
        )

        # --- Diffusion: niche floor plus cost-driven mainstream adoption ---
        #
        # The cost-driven logistic alone deadlocks, and the deadlock is total:
        # learning needs deployment, deployment needs cost parity, cost parity
        # needs learning. The first M1 run showed exactly that -- the low-carbon
        # share fell from 2.5% to 0.03% over seventy years while retirement ate
        # a capacity that was never replaced, because the target share sat at
        # 1/(1+e^18). A technology module that cannot represent any transition
        # is not a technology module.
        #
        # The floor is not a numerical patch. Early low-carbon deployment
        # genuinely does not happen at cost parity: hydro was competitive from
        # the start, and nuclear and solar were both bought for decades by
        # policy and niche markets that did not care about the market price.
        # That niche deployment is what pays for the learning that later makes
        # the mainstream logistic bite -- the standard niche-to-regime story,
        # and how solar actually happened.
        ratio = cost_lowcarbon / params["fossil_cost"]
        mainstream = 1.0 / (
            1.0 + math.exp(params["adoption_sharpness"] * (ratio - 1.0))
        )
        floor = params["niche_share_floor"]
        target_share = floor + (params["lowcarbon_ceiling"] - floor) * mainstream
        target_share = min(target_share, params["lowcarbon_ceiling"])

        # --- Efficiency: energy per unit K-L composite -------------------
        energy_intensity_mult = a_eff ** (-params["efficiency_elasticity"])

        # --- Productivity ------------------------------------------------
        tfp_mult = a_prod ** params["tfp_elasticity"]

        return {
            "knowledge_productivity_idx": a_prod,
            "knowledge_efficiency_idx": a_eff,
            "knowledge_lowcarbon_idx": a_low,
            "lowcarbon_unit_cost": cost_lowcarbon,
            "lowcarbon_cost_ratio": ratio,
            "lowcarbon_target_share": target_share,
            "lowcarbon_capacity": capacity,
            "lowcarbon_cumulative": cumulative,
            "energy_intensity_multiplier": energy_intensity_mult,
            "tfp_multiplier": tfp_mult,
            "frontier_remaining_productivity": (
                view.stock("frontier_pool_productivity") / self.frontier_pool
            ),
        }

    # --------------------------------------------------------------- rates

    def rates(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        # Output is available here: rates run in pass 2, after every module's
        # diagnostics. No lag is needed and none is used.
        y = view.diag("gdp_bn2011ppp")
        rd_total = params["rd_share"] * y

        shares = {
            "productivity": params["rd_share_productivity"],
            "efficiency": params["rd_share_efficiency"],
        }
        shares["lowcarbon"] = max(
            0.0, 1.0 - shares["productivity"] - shares["efficiency"]
        )

        out: dict[str, float] = {}
        for d in DOMAINS:
            a = view.stock(f"knowledge_{d}")
            pool = view.stock(f"frontier_pool_{d}")
            r = rd_total * shares[d]

            frontier_frac = max(pool / self.frontier_pool, 1e-9)
            discovery = (
                params["rnd_productivity"]
                * (r / 1000.0) ** params["rnd_duplication"]
                * a ** params["rnd_shoulders"]
                * frontier_frac ** params["rnd_fishing_out"]
            )
            # Never discover more than remains: the pool is a real constraint,
            # and the engine would raise on a negative stock anyway.
            out[f"discovery_{d}"] = min(discovery, pool * 0.5)
            out[f"obsolescence_{d}"] = params["knowledge_obsolescence"] * a

        # Deployment closes the gap to the target share at a finite rate. The
        # inertia is not a smoothing device: it is the design's point about
        # depreciation clocks (§3.3). Capacity is built by an industry that
        # cannot double overnight, and that constraint is what bounds how fast
        # any transition can physically go, whatever the cost says.
        primary = view.diag("primary_energy_ej")
        capacity = view.stock("lowcarbon_capacity_ej")
        target = view.diag("lowcarbon_target_share") * primary
        out["lowcarbon_deployment"] = params["deployment_speed"] * max(
            target - capacity, 0.0
        )
        out["lowcarbon_retirement"] = params["lowcarbon_retirement_rate"] * capacity

        return out
