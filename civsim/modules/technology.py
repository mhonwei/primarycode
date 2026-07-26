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

    #: The two low-carbon technology families. Names are used to build stock,
    #: flow and parameter keys, so they are part of the interface.
    FAMILIES = ("dispatchable", "modular")

    def __init__(
        self,
        t0: float,
        initial_lowcarbon_ej: float,
        initial_modular_ej: float,
        regions: tuple[str, ...] = ("",),
        frontier_pool: float = 40.0,
    ) -> None:
        self.regions = tuple(regions)
        self.t0 = float(t0)
        self.initial_lowcarbon_ej = float(initial_lowcarbon_ej)
        self.initial_modular_ej = float(initial_modular_ej)
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
        # Low-carbon capacity, split into two technology families.
        #
        # M2 had one. Observed world low-carbon share goes 3.0% (1950) -> 11.3%
        # (1990) -> 12.4% (2000) -> 12.6% (2010) -> 16.4% (2020): a rise, a
        # twenty-year *plateau*, then a resumption. One family with one learning
        # curve and one ceiling cannot produce that at any parameter value --
        # the same structural impossibility as M0's inability to plateau
        # emissions, and the reason this was the worst-modelled channel in the
        # system (11-46% inferred discrepancy, robust loss at every origin).
        #
        # Two families reproduce it without being told to. Dispatchable
        # (hydro, nuclear) learns slowly and runs into a resource and social
        # ceiling, which is what ends the first wave. Modular (wind, solar)
        # starts from a base small enough to be invisible for decades and learns
        # steeply, so it needs that long to climb out and only then bends the
        # curve up again. The plateau is the gap between one saturating and the
        # other arriving -- an emergent interval, not a fitted one.
        #
        # Cost: five parameters. Against §11.6 that is real, and it is spent
        # here because this channel is the weakest in the model by a wide
        # margin and because the shape being missed is qualitative, not a
        # question of degree.
        for fam, init in (
            ("dispatchable", self.initial_lowcarbon_ej),
            ("modular", self.initial_modular_ej),
        ):
            out.append(
                Stock(
                    f"lowcarbon_{fam}_ej",
                    Quantity.ENERGY,
                    init,
                    kind=StockKind.BOUNDARY,
                    description=f"Operating {fam} low-carbon supply, EJ/yr.",
                )
            )
            out.append(
                Stock(
                    f"lowcarbon_{fam}_retired_ej",
                    Quantity.ENERGY,
                    0.0,
                    kind=StockKind.BOUNDARY,
                    description=f"Retired {fam} capacity, EJ/yr equivalent.",
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
        for fam in self.FAMILIES:
            out.append(
                FlowSpec(
                    f"deploy_{fam}",
                    Quantity.ENERGY,
                    "deployment_pool",
                    f"lowcarbon_{fam}_ej",
                )
            )
            out.append(
                FlowSpec(
                    f"retire_{fam}",
                    Quantity.ENERGY,
                    f"lowcarbon_{fam}_ej",
                    f"lowcarbon_{fam}_retired_ej",
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

        out: dict[str, float] = {}
        total_capacity = 0.0
        for fam in self.FAMILIES:
            capacity = view.stock(f"lowcarbon_{fam}_ej")
            cumulative = capacity + view.stock(f"lowcarbon_{fam}_retired_ej")
            initial = (
                self.initial_lowcarbon_ej
                if fam == "dispatchable"
                else self.initial_modular_ej
            )

            # Wright learning on cumulative experience, which is never
            # unlearned -- hence cumulative rather than current capacity.
            lr = params[f"learning_rate_{fam}"]
            b = -math.log(1.0 - lr) / math.log(2.0)
            cost = (
                params[f"lowcarbon_cost_0_{fam}"]
                * (cumulative / initial) ** (-b)
                * a_low ** (-params["rnd_cost_elasticity"])
            )

            # Niche floor plus cost-driven mainstream adoption. The floor is
            # not a numerical patch: early low-carbon deployment genuinely does
            # not happen at cost parity -- hydro was competitive from the start,
            # and nuclear and solar were both bought for decades by policy and
            # niche markets that did not care about the market price. That niche
            # deployment pays for the learning that later makes the mainstream
            # logistic bite. Without it the module deadlocks outright: learning
            # needs deployment, deployment needs parity, parity needs learning.
            ratio = cost / params["fossil_cost"]
            mainstream = 1.0 / (
                1.0 + math.exp(params["adoption_sharpness"] * (ratio - 1.0))
            )
            ceiling = params[f"ceiling_{fam}"]
            floor = min(params[f"niche_floor_{fam}"], ceiling)
            target = floor + (ceiling - floor) * mainstream

            out[f"cost_{fam}"] = cost
            out[f"cost_ratio_{fam}"] = ratio
            out[f"target_share_{fam}"] = target
            out[f"capacity_{fam}"] = capacity
            total_capacity += capacity

        energy_intensity_mult = a_eff ** (-params["efficiency_elasticity"])

        # Absorptive capacity (design §8, L3). Without it a shared global
        # frontier plus Solow accumulation drives full convergence and then
        # overshoot: the first two-region build had the lagging region's capital
        # per head *overtake* the leading region's by 2020 (ratio 4.41 -> 0.88).
        # Poor regions overtaking rich ones is not a subtle calibration error.
        #
        # A region only captures the frontier to the extent it can absorb it
        # (Nelson-Phelps; Benhabib-Spiegel). Absorption rises with the region's
        # own development, so catch-up is possible and self-reinforcing but
        # never automatic, which is what conditional convergence looks like.
        k_head = {
            r: max(view.diag(f"{r}capital_per_head"), 1e-9) for r in self.regions
        }
        frontier_k = max(k_head.values())
        for r in self.regions:
            rel = min(k_head[r] / frontier_k, 1.0)
            absorption = params["absorption_floor"] + (
                1.0 - params["absorption_floor"]
            ) * rel ** params["absorption_theta"]
            out[f"tfp_multiplier_{r}"] = a_prod ** (
                params["tfp_elasticity"] * absorption
            )
            out[f"absorption_{r}"] = absorption
        tfp_mult = a_prod ** params["tfp_elasticity"]

        out.update(
            {
                "knowledge_productivity_idx": a_prod,
                "knowledge_efficiency_idx": a_eff,
                "knowledge_lowcarbon_idx": a_low,
                "lowcarbon_capacity": total_capacity,
                "energy_intensity_multiplier": energy_intensity_mult,
                "tfp_multiplier": tfp_mult,
                "frontier_remaining_productivity": (
                    view.stock("frontier_pool_productivity") / self.frontier_pool
                ),
            }
        )
        return out

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

        # Deployment closes the gap to each family's target share at a finite
        # rate. The inertia is not a smoothing device: it is the design's point
        # about depreciation clocks (§3.3). Capacity is built by an industry
        # that cannot double overnight, and that constraint is what bounds how
        # fast any transition can physically go, whatever the cost says.
        primary = view.diag("primary_energy_ej")
        for fam in self.FAMILIES:
            capacity = view.stock(f"lowcarbon_{fam}_ej")
            target = view.diag(f"target_share_{fam}") * primary
            out[f"deploy_{fam}"] = params[f"deployment_speed_{fam}"] * max(
                target - capacity, 0.0
            )
            out[f"retire_{fam}"] = (
                params[f"retirement_rate_{fam}"] * capacity
            )

        return out
