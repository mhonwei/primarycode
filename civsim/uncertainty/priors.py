"""Parameter priors.

Every parameter is a distribution, never a point (§9.3). The centres below are
set from back-of-envelope consistency with 1950-2020 world aggregates; the
spreads are deliberately wide, because a prior narrow enough to guarantee a good
backtest is just the fit smuggled in through the back door.

`rho` is not sampled directly. The economically meaningful quantity is the
elasticity of substitution sigma between the capital-labour composite and useful
work, and rho = 1 - 1/sigma is a strongly nonlinear reparametrisation of it -- a
symmetric prior on rho is a badly skewed prior on sigma. Sampling sigma and
deriving rho keeps the prior interpretable, which matters when it is the
parameter most likely to be blamed if the backtest disappoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np


class Dist:
    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        raise NotImplementedError

    def log_pdf(self, x: float) -> float:
        """Unnormalised log density. Only ratios are used, so constants drop."""
        raise NotImplementedError

    def scale(self) -> float:
        """Characteristic width, used to size SMC proposal steps."""
        raise NotImplementedError

    def describe(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class Fixed(Dist):
    value: float

    def sample(self, rng, n):
        return np.full(n, self.value)

    def log_pdf(self, x):
        return 0.0 if x == self.value else -np.inf

    def scale(self):
        return 0.0

    def describe(self):
        return f"fixed({self.value:g})"


@dataclass(frozen=True)
class Normal(Dist):
    mu: float
    sd: float

    def sample(self, rng, n):
        return rng.normal(self.mu, self.sd, n)

    def log_pdf(self, x):
        return -0.5 * ((x - self.mu) / self.sd) ** 2

    def scale(self):
        return self.sd

    def describe(self):
        return f"N({self.mu:g}, {self.sd:g})"


@dataclass(frozen=True)
class TruncNormal(Dist):
    mu: float
    sd: float
    lo: float = -np.inf
    hi: float = np.inf

    def sample(self, rng, n):
        out = rng.normal(self.mu, self.sd, n)
        # Resample rather than clip: clipping piles probability mass on the
        # bounds, which then shows up as a spurious spike in the fan chart.
        for _ in range(64):
            bad = (out < self.lo) | (out > self.hi)
            if not bad.any():
                break
            out[bad] = rng.normal(self.mu, self.sd, int(bad.sum()))
        return np.clip(out, self.lo, self.hi)

    def log_pdf(self, x):
        if x < self.lo or x > self.hi:
            return -np.inf
        return -0.5 * ((x - self.mu) / self.sd) ** 2

    def scale(self):
        return self.sd

    def describe(self):
        return f"N({self.mu:g}, {self.sd:g})[{self.lo:g}, {self.hi:g}]"


@dataclass(frozen=True)
class Uniform(Dist):
    lo: float
    hi: float

    def sample(self, rng, n):
        return rng.uniform(self.lo, self.hi, n)

    def log_pdf(self, x):
        return 0.0 if self.lo <= x <= self.hi else -np.inf

    def scale(self):
        return (self.hi - self.lo) / np.sqrt(12.0)

    def describe(self):
        return f"U({self.lo:g}, {self.hi:g})"


#: M1 world prior. Keys map onto the parameter names the modules read.
M0_PRIOR: dict[str, Dist] = {
    # --- production -------------------------------------------------------
    "alpha": TruncNormal(0.35, 0.03, 0.20, 0.50),
    "beta": TruncNormal(0.70, 0.05, 0.40, 0.92),
    "sigma_kl_u": Uniform(0.45, 0.95),  # rho derived; see derive_params
    # The only regional parameter. Everything else -- the energy service
    # ladder, the demographic transition, the whole technology layer -- is one
    # global function that both regions sit on at different points. That is what
    # lets the cross-section identify curve shapes without doubling the budget.
    "saving_rate_hi_": TruncNormal(0.22, 0.02, 0.13, 0.32),
    "saving_rate_lo_": TruncNormal(0.27, 0.03, 0.15, 0.40),
    "depreciation_rate": TruncNormal(0.050, 0.008, 0.025, 0.080),
    "capital_output_ratio": TruncNormal(3.0, 0.3, 2.0, 4.5),
    # --- technology (M1) --------------------------------------------------
    # Semi-endogenous R&D. `rnd_duplication` < 1 is Jones's duplication
    # externality, `rnd_shoulders` < 1 diminishing returns to standing on
    # shoulders, `rnd_fishing_out` > 0 the depleting frontier. Together they
    # guarantee no scale effect and hence no manufactured singularity.
    "rd_share": TruncNormal(0.015, 0.004, 0.004, 0.030),
    "rd_share_productivity": TruncNormal(0.60, 0.08, 0.35, 0.80),
    "rd_share_efficiency": TruncNormal(0.20, 0.06, 0.05, 0.40),
    "rnd_productivity": TruncNormal(0.040, 0.020, 0.005, 0.120),
    "rnd_duplication": TruncNormal(0.50, 0.12, 0.20, 0.85),
    "rnd_shoulders": TruncNormal(0.30, 0.12, 0.00, 0.70),
    "rnd_fishing_out": TruncNormal(0.50, 0.20, 0.05, 1.20),
    "knowledge_obsolescence": TruncNormal(0.003, 0.0015, 0.0, 0.010),
    "tfp_elasticity": TruncNormal(1.00, 0.25, 0.30, 1.80),
    # Absorptive capacity: how much of the global frontier a region captures,
    # as a function of its development relative to the leader. The floor is what
    # a region gets with no absorptive capacity at all; theta sets how fast the
    # rest is earned. Two parameters, spent to remove a qualitative failure --
    # the lagging region overtaking the leader -- not to improve a fit.
    "absorption_floor": TruncNormal(0.45, 0.12, 0.15, 0.80),
    "absorption_theta": TruncNormal(0.60, 0.25, 0.10, 1.50),
    "efficiency_elasticity": TruncNormal(0.50, 0.25, 0.05, 1.20),
    # Wright learning, per technology family.
    #
    # M2 had one low-carbon technology. Observed world low-carbon share rises,
    # then sits on a twenty-year plateau (11.3% in 1990 -> 12.6% in 2010), then
    # resumes. One family with one learning rate and one ceiling cannot produce
    # that at any parameter value, which is why this was the model's worst
    # channel. Two families can, and the plateau then emerges as the gap between
    # one saturating and the other arriving rather than being fitted.
    #
    # Dispatchable = hydro + nuclear: civil-engineering learning rates near
    # zero, competitive from the start, and a hard resource-and-social ceiling.
    # Modular = wind + solar: steep modular learning, a starting cost far above
    # parity, and a base so small it takes decades of doublings to matter.
    "learning_rate_dispatchable": TruncNormal(0.06, 0.03, 0.01, 0.15),
    "learning_rate_modular": TruncNormal(0.22, 0.05, 0.10, 0.35),
    "lowcarbon_cost_0_dispatchable": TruncNormal(1.3, 0.3, 0.7, 2.5),
    "lowcarbon_cost_0_modular": TruncNormal(20.0, 8.0, 5.0, 45.0),
    "ceiling_dispatchable": TruncNormal(0.18, 0.05, 0.08, 0.35),
    "ceiling_modular": TruncNormal(0.85, 0.08, 0.50, 0.98),
    "niche_floor_dispatchable": TruncNormal(0.030, 0.010, 0.010, 0.060),
    "niche_floor_modular": TruncNormal(0.0020, 0.0015, 0.0002, 0.0080),
    "deployment_speed_dispatchable": TruncNormal(0.050, 0.020, 0.010, 0.120),
    "deployment_speed_modular": TruncNormal(0.100, 0.040, 0.020, 0.250),
    "retirement_rate_dispatchable": TruncNormal(0.020, 0.006, 0.008, 0.040),
    "retirement_rate_modular": TruncNormal(0.040, 0.010, 0.020, 0.070),
    "fossil_cost": Fixed(1.0),  # numeraire
    "rnd_cost_elasticity": TruncNormal(0.30, 0.15, 0.02, 0.80),
    # Softened from 6.0. At sharpness 6 the logistic is effectively a step: a
    # technology at 1.9x parity gets a 0.5% share, when the historical record
    # says such a technology is already visibly deploying. The transition is a
    # gradient, not a threshold.
    "adoption_sharpness": TruncNormal(2.5, 1.0, 0.8, 6.0),
    "initial_modular_share": TruncNormal(0.0003, 0.0002, 0.00005, 0.0010),
    "initial_lowcarbon_share": TruncNormal(0.030, 0.006, 0.015, 0.050),
    # --- energy -----------------------------------------------------------
    # Energy service demand per unit of capital, saturating in development.
    # This is the energy ladder; it is what allows intensity to rise and then
    # fall rather than only ever falling.
    "energy_service_half": TruncNormal(80000.0, 30000.0, 20000.0, 220000.0),
    "energy_service_theta": TruncNormal(1.00, 0.30, 0.30, 2.20),
    "conv_eff_initial": TruncNormal(0.080, 0.015, 0.040, 0.130),
    "conv_eff_ceiling": TruncNormal(0.200, 0.030, 0.130, 0.320),
    "conv_eff_rate": TruncNormal(0.60, 0.30, 0.05, 1.80),
    # --- demography (M1: three compartments) ------------------------------
    # Fertility is per 1000 working-age persons, not per 1000 total, because
    # that is the population actually at risk of giving birth. Centres derived
    # from world CBR 37 -> 17.5 per 1000 total over 1950-2020, rebased on the
    # observed working-age share.
    "fert_max": TruncNormal(75.0, 8.0, 55.0, 100.0),
    "fert_min": TruncNormal(18.0, 4.0, 8.0, 30.0),
    "fert_half": TruncNormal(19000.0, 4000.0, 8000.0, 40000.0),
    "fert_theta": TruncNormal(2.17, 0.40, 1.00, 3.60),
    "mort_max": TruncNormal(40.0, 6.0, 25.0, 60.0),
    "mort_min": TruncNormal(6.0, 1.5, 2.5, 11.0),
    "mort_half": TruncNormal(14800.0, 3000.0, 6000.0, 28000.0),
    "mort_theta": TruncNormal(2.32, 0.45, 1.00, 4.00),
    # Compartment mortality relative to the common scale. The old-age ratio is
    # what makes the aggregate crude death rate rise as the population ages --
    # the dynamic M0 structurally could not produce.
    "mort_ratio_youth": TruncNormal(0.50, 0.15, 0.15, 1.00),
    "mort_ratio_working": TruncNormal(0.40, 0.10, 0.15, 0.75),
    "mort_ratio_old": TruncNormal(6.00, 2.00, 2.00, 14.00),
    # --- carbon -----------------------------------------------------------
    # Intensity of *fossil* primary energy; the observed decline is now produced
    # by the low-carbon share rather than assumed as an exponential.
    "carbon_intensity_fossil": TruncNormal(0.02115, 0.0012, 0.016, 0.027),
    # Land-use change, absent in M0 and diagnosed from its residuals.
    "land_use_emissions_gtc": TruncNormal(1.40, 0.40, 0.40, 2.60),
    "uptake_fast": TruncNormal(0.55, 0.05, 0.35, 0.72),
    "uptake_slow": TruncNormal(0.0010, 0.0010, 0.0, 0.0060),
    "ocean_uptake_share": TruncNormal(0.60, 0.05, 0.40, 0.80),
    # --- structural constants --------------------------------------------
    "participation_rate": Fixed(0.70),
    "labour_share": Fixed(0.58),
    "tax_rate": Fixed(0.15),
}


def derive_params(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Add parameters that are deterministic functions of sampled ones."""
    out = dict(raw)
    sigma = out["sigma_kl_u"]
    if sigma <= 0:
        raise ValueError(f"elasticity of substitution must be > 0, got {sigma}")
    out["rho"] = 1.0 - 1.0 / sigma
    return out


def sample_prior(
    rng: np.random.Generator,
    n: int,
    prior: Mapping[str, Dist] | None = None,
) -> list[dict[str, Any]]:
    p = dict(prior or M0_PRIOR)
    cols = {k: d.sample(rng, n) for k, d in p.items()}
    return [
        derive_params({k: float(v[i]) for k, v in cols.items()}) for i in range(n)
    ]


def describe_prior(prior: Mapping[str, Dist] | None = None) -> str:
    p = dict(prior or M0_PRIOR)
    return "\n".join(f"  {k:28s} {d.describe()}" for k, d in sorted(p.items()))


def free_names(prior: Mapping[str, Dist] | None = None) -> list[str]:
    """Names of parameters that actually vary (Fixed ones are excluded)."""
    p = dict(prior or M0_PRIOR)
    return [k for k, d in sorted(p.items()) if not isinstance(d, Fixed)]


def log_prior(
    theta: Mapping[str, Any], prior: Mapping[str, Dist] | None = None
) -> float:
    p = dict(prior or M0_PRIOR)
    total = 0.0
    for k, d in p.items():
        if isinstance(d, Fixed):
            continue
        total += d.log_pdf(float(theta[k]))
        if not np.isfinite(total):
            return -np.inf
    return total


def prior_scales(prior: Mapping[str, Dist] | None = None) -> np.ndarray:
    p = dict(prior or M0_PRIOR)
    return np.array([p[k].scale() for k in free_names(p)])


def vector_to_params(
    x: np.ndarray,
    base: Mapping[str, Any],
    prior: Mapping[str, Dist] | None = None,
) -> dict[str, Any]:
    """Rebuild a full parameter dict from a free-parameter vector."""
    out = dict(base)
    for k, v in zip(free_names(prior), x):
        out[k] = float(v)
    return derive_params(out)


def params_to_vector(
    theta: Mapping[str, Any], prior: Mapping[str, Dist] | None = None
) -> np.ndarray:
    return np.array([float(theta[k]) for k in free_names(prior)])
