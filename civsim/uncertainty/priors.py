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


#: M0 world prior. Keys map onto the parameter names the modules read.
M0_PRIOR: dict[str, Dist] = {
    # --- production -------------------------------------------------------
    "alpha": TruncNormal(0.35, 0.03, 0.20, 0.50),
    "beta": TruncNormal(0.70, 0.05, 0.40, 0.92),
    "sigma_kl_u": Uniform(0.45, 0.95),  # rho derived; see derive_params
    "tfp_growth": Normal(0.005, 0.003),
    "saving_rate": TruncNormal(0.24, 0.02, 0.15, 0.35),
    "depreciation_rate": TruncNormal(0.050, 0.008, 0.025, 0.080),
    "capital_output_ratio": TruncNormal(3.0, 0.3, 2.0, 4.5),
    # --- energy -----------------------------------------------------------
    # Autonomous drift in energy required per unit of K-L composite. Centred on
    # zero: "no autonomous trend" is the neutral null, and the efficiency and
    # composition stories that would move it point in both directions.
    #
    # Revised at M0 after a prior predictive check on the calibration window
    # (1950-1990 only) showed the original centre of -0.005 put the *entire*
    # prior below observed primary energy -- p95 of 237 EJ against 320 EJ
    # observed in 1990. That centre came from a back-of-envelope that took the
    # 2020 capital stock from an assumed capital-output ratio instead of from
    # the model's own accumulation, and was simply wrong. Recentred on zero
    # rather than on the data-preferred 0.0014, which would be fitting the
    # centre rather than correcting an error. Logged in docs/model-changelog.md.
    "energy_per_kl_growth": Normal(0.0, 0.005),
    "conv_eff_initial": TruncNormal(0.080, 0.015, 0.040, 0.130),
    "conv_eff_ceiling": TruncNormal(0.200, 0.030, 0.130, 0.320),
    "conv_eff_rate": TruncNormal(0.012, 0.005, 0.002, 0.030),
    # --- demography -------------------------------------------------------
    "cbr_min": TruncNormal(10.0, 2.0, 5.0, 16.0),
    "cbr_max": TruncNormal(45.0, 3.0, 36.0, 55.0),
    "cbr_half": TruncNormal(21000.0, 4000.0, 9000.0, 38000.0),
    "cbr_theta": TruncNormal(1.93, 0.30, 1.00, 3.20),
    "cdr_min": TruncNormal(7.0, 1.0, 4.5, 10.5),
    "cdr_max": TruncNormal(26.0, 3.0, 17.0, 36.0),
    "cdr_half": TruncNormal(13300.0, 2500.0, 6000.0, 24000.0),
    "cdr_theta": TruncNormal(3.04, 0.50, 1.50, 5.00),
    # --- carbon -----------------------------------------------------------
    "carbon_intensity_0": TruncNormal(0.02073, 0.0012, 0.016, 0.026),
    "carbon_intensity_decline": TruncNormal(0.0027, 0.0010, 0.0, 0.0070),
    "uptake_fast": TruncNormal(0.55, 0.05, 0.35, 0.72),
    "uptake_slow": TruncNormal(0.0010, 0.0010, 0.0, 0.0060),
    "ocean_uptake_share": TruncNormal(0.60, 0.05, 0.40, 0.80),
    # --- structural constants --------------------------------------------
    # Participation cancels out of every normalised ratio in M0; it is kept
    # explicit so M1 can swap in a working-age share without an interface change.
    "participation_rate": Fixed(0.45),
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
