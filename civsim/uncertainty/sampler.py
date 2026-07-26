"""Monte Carlo over the prior, then importance-weighting on the calibration window.

M0 does not run MCMC. With a 5-yearly snapshot and ~25 parameters, self-normalised
importance sampling from the prior is enough to produce a genuine posterior
predictive distribution, and it has one property that matters more here than
efficiency: the calibration data enters at exactly one place -- :func:`log_weights`
-- so it is easy to verify by inspection that the test window never touches the
weights. An MCMC sampler threading likelihood evaluations through an inner loop
would make that audit much harder for no gain at this resolution.

The likelihood scale
--------------------
The scale used below is *not* observation error. Setting it to the true
measurement precision of, say, Mauna Loa CO2 would make the likelihood
astronomically peaked, collapse the effective sample size to one draw, and
produce a fan chart of zero width around a wrong trajectory -- overconfidence
manufactured by an accounting error. The scale that belongs here is
observation error *plus acknowledged structural error*: how far a
four-box, single-region model can be from the world and still be considered
consistent with it. That term dominates, and it is declared explicitly rather
than tuned until the answer looks good.

Failed draws are reported, not silently dropped. A high failure rate means the
prior puts mass on parameter combinations the model cannot integrate, which is
information about the prior, not noise to be swept up.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np

from ..core.engine import Trajectory
from ..core.financial import SectorBalanceViolation
from ..core.ledger import ConservationViolation
from ..data.grading import Grade
from ..data.registry import Snapshot
from ..model import OBSERVED_SERIES, build_engine

#: Likelihood scale by data grade (relative, log space). Observation component.
GRADE_OBS_SCALE: dict[Grade, float] = {
    Grade.A: 0.01,
    Grade.B: 0.04,
    Grade.C: 0.10,
}

#: Acknowledged structural error of an M0 single-region four-box model.
#: Dominates the observation term by design; see module docstring.
STRUCTURAL_SCALE = 0.06

#: Correlation length of the structural discrepancy, in years.
#:
#: This is the parameter that stops the likelihood being wrong by an order of
#: magnitude. The error of a deterministic simulator against the world is
#: *persistent*: if the model runs 8% high in 1975 it runs about 8% high in 1976
#: as well. Treating each calendar year as an independent draw -- the default
#: anyone writes first -- multiplies the apparent information in a smooth
#: 40-year series by roughly the number of years in it, producing a likelihood
#: so peaked that importance sampling collapses onto a single particle and the
#: fan chart comes out with no width at all. That failure is not subtle when you
#: look for it (ESS of 1, PIT mass entirely in the tails) and completely
#: invisible if you do not.
#:
#: Modelling the discrepancy as a correlated process is the standard treatment
#: (Kennedy & O'Hagan 2001). 25 years is chosen as roughly the timescale over
#: which the structural sources of error here -- a single region, no age
#: structure, one carbon reduced form -- would plausibly change character. With
#: it, nine calibration points on a smooth series count for about two
#: independent observations, which is the honest figure.
DISCREPANCY_CORR_YEARS = 25.0


def likelihood_scale(grade: Grade, structural: float = STRUCTURAL_SCALE) -> float:
    return math.sqrt(GRADE_OBS_SCALE[grade] ** 2 + structural**2)


def discrepancy_covariance(
    years: np.ndarray,
    sds: np.ndarray,
    corr_years: float = DISCREPANCY_CORR_YEARS,
) -> np.ndarray:
    """Exponential-kernel covariance for a persistent model-world discrepancy."""
    dt = np.abs(years[:, None] - years[None, :])
    corr = np.exp(-dt / corr_years)
    sigma = corr * np.outer(sds, sds)
    # Nugget: keeps the Cholesky well conditioned when points are dense.
    sigma[np.diag_indices_from(sigma)] += 1e-10
    return sigma


def effective_n_obs(
    years: np.ndarray, corr_years: float = DISCREPANCY_CORR_YEARS
) -> float:
    """How many independent observations a correlated series is worth."""
    dt = np.abs(years[:, None] - years[None, :])
    corr = np.exp(-dt / corr_years)
    return float(len(years) ** 2 / np.sum(corr))


@dataclass
class Ensemble:
    times: np.ndarray
    #: series name -> (n_members, n_times)
    paths: dict[str, np.ndarray]
    params: list[dict[str, Any]]
    n_requested: int
    failures: list[tuple[int, str]] = field(default_factory=list)
    weights: np.ndarray | None = None

    @property
    def n_members(self) -> int:
        return len(self.params)

    @property
    def failure_rate(self) -> float:
        return len(self.failures) / self.n_requested if self.n_requested else 0.0

    def failure_summary(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for _, kind in self.failures:
            out[kind] = out.get(kind, 0) + 1
        return out

    def at(self, series: str, years: Sequence[float]) -> np.ndarray:
        idx = {float(t): i for i, t in enumerate(self.times)}
        cols = [idx[float(y)] for y in years]
        return self.paths[series][:, cols]


def run_ensemble(
    param_sets: Sequence[Mapping[str, Any]],
    snapshot: Snapshot,
    t0: float = 1950.0,
    t1: float = 2020.0,
    series: Sequence[str] = OBSERVED_SERIES,
    check_conservation: bool = True,
) -> Ensemble:
    """Run one trajectory per parameter draw, collecting the observed series."""
    times: np.ndarray | None = None
    collected: dict[str, list[np.ndarray]] = {s: [] for s in series}
    kept: list[dict[str, Any]] = []
    failures: list[tuple[int, str]] = []

    for i, p in enumerate(param_sets):
        try:
            eng = build_engine(
                p, snapshot, t0=t0, check_conservation=check_conservation
            )
            traj: Trajectory = eng.run(t0, t1)
            vals = {s: traj.series(s) for s in series}
        except (ConservationViolation, SectorBalanceViolation):
            # These are model bugs, not bad draws. Never swallow them.
            raise
        except (ValueError, ArithmeticError, RuntimeError, KeyError) as e:
            failures.append((i, type(e).__name__))
            continue

        bad = any(not np.all(np.isfinite(v)) for v in vals.values())
        if bad:
            failures.append((i, "NonFinite"))
            continue

        if times is None:
            times = traj.times
        for s in series:
            collected[s].append(vals[s])
        kept.append(dict(p))

    if times is None:
        raise RuntimeError(
            f"every one of {len(param_sets)} draws failed to integrate. "
            f"Failure modes: {dict((k, sum(1 for _, x in failures if x == k)) for k in set(x for _, x in failures))}"
        )

    return Ensemble(
        times=times,
        paths={s: np.vstack(collected[s]) for s in series},
        params=kept,
        n_requested=len(param_sets),
        failures=failures,
    )


# --- per-series discrepancy scale (M2) --------------------------------------
#
# M1's likelihood gave every series the same 6% structural scale. That is not a
# conservative default, it is an assertion -- that the model is equally wrong
# about population and about the low-carbon share -- and it was false by a
# factor of five. A series fitted at 27% MAPE then contributes residuals five
# standard deviations wide, dominates the joint likelihood, and drags shared
# parameters away from where the series it *can* fit would put them. M1 lost
# M0's one robust win that way.
#
# Assigning a scale per series by hand would fix the symptom by fitting the
# likelihood, which is worse. The right move is to treat each series' scale as
# unknown and integrate it out. With an inverse-gamma prior on sigma^2 the
# integral is analytic and the Gaussian becomes a multivariate Student-t:
#
#   log p(r) = -n/2 log(2pi) - 1/2 log|S| + a log b - lgamma(a)
#              + lgamma(a + n/2) - (a + n/2) log(b + Q/2)
#
# with Q = r' S^-1 r and S the correlation shape. The decisive difference is
# that the residual enters through log(b + Q/2) rather than through Q: a badly
# fitted series is charged a logarithmic penalty instead of a quadratic one, so
# it reports "I am a poorly modelled channel" instead of overwhelming the rest.
#
# This adds no sampled parameters. It also yields a *diagnostic* worth more than
# the fix -- the posterior scale per series is a direct estimate of how wrong
# the model is in each channel, which is exactly what a structural-error budget
# needs and what nothing in M0 or M1 could report.

#: Inverse-gamma prior on the per-series discrepancy variance.
#: a=2 gives 4 degrees of freedom -- heavy tailed on purpose, since the whole
#: point is to tolerate a channel being far more wrong than expected.
#: b is set so E[sigma^2] = b/(a-1) matches STRUCTURAL_SCALE^2.
DISCREPANCY_IG_A = 2.0
DISCREPANCY_IG_B = (DISCREPANCY_IG_A - 1.0) * STRUCTURAL_SCALE**2


def _shape_matrix(
    years: np.ndarray,
    obs_sds: np.ndarray,
    structural_ref: float,
    corr_years: float,
) -> np.ndarray:
    """Correlation shape with grade-driven extra variance on the diagonal.

    The overall scale is integrated out, so what remains here is *relative*
    structure: the correlation kernel, plus per-point slack proportional to how
    observational that point is. Grade therefore still distinguishes points
    within a series -- pre-1959 ice-core CO2 gets more slack than Mauna Loa --
    while the series-wide scale is inferred rather than asserted.
    """
    dt = np.abs(years[:, None] - years[None, :])
    shape = np.exp(-dt / corr_years)
    shape[np.diag_indices_from(shape)] += (obs_sds / structural_ref) ** 2 + 1e-10
    return shape


@dataclass(frozen=True)
class SeriesLik:
    """Per-series likelihood pieces, kept so the scale can be reported."""

    name: str
    quad: np.ndarray  # r' S^-1 r per member
    n: int
    logdet: float

    def loglik(self, a: float, b: float) -> np.ndarray:
        return (
            -0.5 * self.n * math.log(2.0 * math.pi)
            - 0.5 * self.logdet
            + a * math.log(b)
            - math.lgamma(a)
            + math.lgamma(a + 0.5 * self.n)
            - (a + 0.5 * self.n) * np.log(b + 0.5 * self.quad)
        )

    def posterior_scale(self, a: float, b: float) -> np.ndarray:
        """Posterior mean of sigma given the residuals -- the inferred scale."""
        denom = a + 0.5 * self.n - 1.0
        return np.sqrt((b + 0.5 * self.quad) / denom)


def series_likelihoods(
    paths: Mapping[str, np.ndarray],
    times: np.ndarray,
    calibration_obs: Mapping[str, Any],
    snapshot: Snapshot,
    structural: float = STRUCTURAL_SCALE,
    corr_years: float = DISCREPANCY_CORR_YEARS,
) -> list[SeriesLik]:
    """Quadratic forms per series, against calibration-window data only.

    `calibration_obs` must come from :meth:`Holdout.calibration`. Nothing here
    can see the test window, and that is the single audit point the whole
    hold-out discipline rests on.
    """
    idx = {float(t): i for i, t in enumerate(times)}
    n_members = next(iter(paths.values())).shape[0]
    out: list[SeriesLik] = []

    for name, obs in calibration_obs.items():
        meta = snapshot.series(name).meta
        cols = [idx[float(y)] for y in obs.years]
        model = paths[name][:, cols]
        with np.errstate(divide="ignore", invalid="ignore"):
            resid = np.log(model) - np.log(obs.values)[None, :]

        obs_sds = np.array(
            [GRADE_OBS_SCALE[meta.grade_at(float(y))] for y in obs.years]
        )
        shape = _shape_matrix(obs.years, obs_sds, structural, corr_years)
        chol = np.linalg.cholesky(shape)
        logdet = 2.0 * float(np.sum(np.log(np.diag(chol))))

        finite = np.all(np.isfinite(resid), axis=1)
        quad = np.full(n_members, np.inf)
        if finite.any():
            z = np.linalg.solve(chol, resid[finite].T)
            quad[finite] = np.sum(z**2, axis=0)
        out.append(SeriesLik(name, quad, len(obs.years), logdet))

    return out


# --- cross-series error correlation (M3) ------------------------------------
#
# M2 gave each series its own discrepancy scale but still treated series as
# conditionally independent. They are not, and not marginally: emissions are
# computed *from* energy in this model, so a particle that runs energy 20% high
# runs emissions high by construction. Scoring both as independent evidence
# counts the same error twice, and with nine series most of which sit on one
# causal chain -- capital drives energy drives emissions drives concentration --
# the joint likelihood is far sharper than the information warrants. That is the
# same class of error as M1's uniform scale, one level up.
#
# The fix is the matrix generalisation of what M2 did. Stack residuals into a
# p x n matrix (series by year), model it as matrix-normal with a separable
# covariance Sigma (x) C, put an inverse-Wishart prior on the p x p cross-series
# covariance Sigma, and integrate it out. The result is a matrix-t:
#
#   log p(R) = c - (nu + n)/2 * log|Psi + R C^-1 R'| + (nu/2) log|Psi|
#              - (p/2) log|C| + logGamma_p((nu+n)/2) - logGamma_p(nu/2)
#
# The decisive term is a *determinant*, where M2 had a sum of per-series scalar
# penalties. If two series' residuals point the same way, R C^-1 R' is nearly
# singular in that direction and the determinant barely grows -- aligned errors
# stop being counted as separate evidence. If they are orthogonal, it grows the
# full amount and they count separately, which is correct.
#
# It also yields the diagnostic that was missing: the posterior cross-series
# error correlation matrix, which says outright which channels are failing
# together and therefore how much of the apparent evidence was ever independent.

#: Inverse-Wishart prior on the cross-series discrepancy covariance.
#: nu = p + 2 is the weakest proper prior with a finite mean; Psi is set so
#: E[Sigma] = STRUCTURAL_SCALE^2 * I, i.e. the M1 assumption as a prior mean
#: rather than as an assertion.
def _iw_prior(p: int, structural: float) -> tuple[float, np.ndarray]:
    nu = p + 2.0
    psi = (nu - p - 1.0) * structural**2 * np.eye(p)
    return nu, psi


def _log_multigamma(a: float, p: int) -> float:
    return 0.25 * p * (p - 1) * math.log(math.pi) + sum(
        math.lgamma(a + 0.5 * (1 - j)) for j in range(1, p + 1)
    )


def residual_tensor(
    paths: Mapping[str, np.ndarray],
    times: np.ndarray,
    calibration_obs: Mapping[str, Any],
    snapshot: Snapshot,
    structural: float = STRUCTURAL_SCALE,
) -> tuple[np.ndarray, list[str], np.ndarray]:
    """Grade-whitened residuals as (n_members, n_series, n_years).

    Grade enters here rather than in the covariance. The Kronecker structure
    needs one time-covariance shared by every series, but observation error
    varies by series *and* year (pre-1959 ice-core CO2 against Mauna Loa).
    Dividing each residual by its own known observation slack before the
    separable model sees it keeps grade meaningful without breaking
    separability -- it is pre-whitening of a known error, not an approximation
    of the unknown one.
    """
    names = sorted(calibration_obs)
    grids = {tuple(calibration_obs[n].years) for n in names}
    if len(grids) != 1:
        raise ValueError(
            "cross-series covariance requires one shared year grid; got "
            f"{len(grids)} distinct grids. Align the snapshot or fall back to "
            "the per-series likelihood."
        )
    years = np.asarray(next(iter(grids)), dtype=float)
    idx = {float(t): i for i, t in enumerate(times)}
    cols = [idx[float(y)] for y in years]

    n_members = next(iter(paths.values())).shape[0]
    R = np.empty((n_members, len(names), len(years)))
    for i, name in enumerate(names):
        obs = calibration_obs[name]
        meta = snapshot.series(name).meta
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.log(paths[name][:, cols]) - np.log(obs.values)[None, :]
        slack = np.array(
            [
                math.sqrt(
                    1.0
                    + (GRADE_OBS_SCALE[meta.grade_at(float(y))] / structural) ** 2
                )
                for y in years
            ]
        )
        R[:, i, :] = r / slack[None, :]
    return R, names, years


def loglik_paths(
    paths: Mapping[str, np.ndarray],
    times: np.ndarray,
    calibration_obs: Mapping[str, Any],
    snapshot: Snapshot,
    structural: float = STRUCTURAL_SCALE,
    corr_years: float = DISCREPANCY_CORR_YEARS,
    cross_series: bool = True,
) -> np.ndarray:
    """Joint log-likelihood against calibration-window data only.

    With `cross_series` the errors are modelled as correlated across series and
    that correlation is integrated out (matrix-t). Setting it False recovers the
    M2 per-series marginal-t, which is kept so the two can be compared rather
    than swapped in on faith.
    """
    if not cross_series:
        liks = series_likelihoods(
            paths, times, calibration_obs, snapshot, structural, corr_years
        )
        total = np.zeros(next(iter(paths.values())).shape[0])
        for lk in liks:
            total += lk.loglik(DISCREPANCY_IG_A, DISCREPANCY_IG_B)
        total[~np.isfinite(total)] = -np.inf
        return total

    R, names, years = residual_tensor(
        paths, times, calibration_obs, snapshot, structural
    )
    n_members, p, n = R.shape
    nu, psi = _iw_prior(p, structural)

    dt = np.abs(years[:, None] - years[None, :])
    C = np.exp(-dt / corr_years) + 1e-10 * np.eye(n)
    C_chol = np.linalg.cholesky(C)
    logdet_C = 2.0 * float(np.sum(np.log(np.diag(C_chol))))

    const = (
        -0.5 * n * p * math.log(math.pi)
        + _log_multigamma(0.5 * (nu + n), p)
        - _log_multigamma(0.5 * nu, p)
        + 0.5 * nu * float(np.linalg.slogdet(psi)[1])
        - 0.5 * p * logdet_C
    )

    finite = np.all(np.isfinite(R), axis=(1, 2))
    out = np.full(n_members, -np.inf)
    if finite.any():
        Rf = R[finite]
        # Z = R C^-1/2, so G = Z Z' = R C^-1 R'
        Z = np.linalg.solve(C_chol, Rf.transpose(0, 2, 1)).transpose(0, 2, 1)
        G = np.einsum("mik,mjk->mij", Z, Z)
        sign, logdet = np.linalg.slogdet(psi[None, :, :] + G)
        ok = sign > 0
        vals = np.full(Rf.shape[0], -np.inf)
        vals[ok] = const - 0.5 * (nu + n) * logdet[ok]
        out[finite] = vals

    out[~np.isfinite(out)] = -np.inf
    return out


def inferred_error_covariance(
    paths: Mapping[str, np.ndarray],
    times: np.ndarray,
    calibration_obs: Mapping[str, Any],
    snapshot: Snapshot,
    structural: float = STRUCTURAL_SCALE,
    corr_years: float = DISCREPANCY_CORR_YEARS,
) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Posterior mean cross-series error covariance, and its correlation form.

    The correlation matrix is the point of the exercise: it says which channels
    fail together, and therefore how much of the joint likelihood's apparent
    evidence was ever independent.
    """
    R, names, years = residual_tensor(
        paths, times, calibration_obs, snapshot, structural
    )
    n_members, p, n = R.shape
    nu, psi = _iw_prior(p, structural)

    dt = np.abs(years[:, None] - years[None, :])
    C = np.exp(-dt / corr_years) + 1e-10 * np.eye(n)
    C_chol = np.linalg.cholesky(C)

    finite = np.all(np.isfinite(R), axis=(1, 2))
    if not finite.any():
        nan = np.full((p, p), np.nan)
        return names, nan, nan
    Rf = R[finite]
    Z = np.linalg.solve(C_chol, Rf.transpose(0, 2, 1)).transpose(0, 2, 1)
    G = np.einsum("mik,mjk->mij", Z, Z)
    denom = nu + n - p - 1.0
    sigma = np.median((psi[None, :, :] + G) / denom, axis=0)

    sd = np.sqrt(np.clip(np.diag(sigma), 1e-300, None))
    corr = sigma / np.outer(sd, sd)
    return names, sigma, corr


def inferred_discrepancy(
    paths: Mapping[str, np.ndarray],
    times: np.ndarray,
    calibration_obs: Mapping[str, Any],
    snapshot: Snapshot,
    structural: float = STRUCTURAL_SCALE,
    corr_years: float = DISCREPANCY_CORR_YEARS,
) -> dict[str, float]:
    """Inferred structural error per series -- how wrong the model is, by channel."""
    liks = series_likelihoods(
        paths, times, calibration_obs, snapshot, structural, corr_years
    )
    out: dict[str, float] = {}
    for lk in liks:
        s = lk.posterior_scale(DISCREPANCY_IG_A, DISCREPANCY_IG_B)
        s = s[np.isfinite(s)]
        out[lk.name] = float(np.median(s)) if s.size else float("nan")
    return out


def log_weights(
    ens: Ensemble,
    calibration_obs: Mapping[str, Any],
    snapshot: Snapshot,
    structural: float = STRUCTURAL_SCALE,
    corr_years: float = DISCREPANCY_CORR_YEARS,
) -> np.ndarray:
    return loglik_paths(
        ens.paths, ens.times, calibration_obs, snapshot, structural, corr_years
    )


def normalise_weights(logw: np.ndarray) -> np.ndarray:
    m = np.max(logw[np.isfinite(logw)]) if np.any(np.isfinite(logw)) else 0.0
    w = np.exp(logw - m)
    w[~np.isfinite(w)] = 0.0
    s = w.sum()
    if s <= 0:
        raise RuntimeError(
            "all importance weights are zero: no prior draw is remotely "
            "consistent with the calibration data. Either the prior is in the "
            "wrong place or the model is structurally wrong -- widening the "
            "likelihood scale to make this go away would be fitting by fiat."
        )
    return w / s


def effective_sample_size(w: np.ndarray) -> float:
    return float(1.0 / np.sum(w**2))


def systematic_resample(
    w: np.ndarray, n: int, rng: np.random.Generator
) -> np.ndarray:
    """Low-variance resampling to an equal-weight ensemble of size n.

    Downstream scoring (CRPS, PIT) assumes equal weights; resampling once here
    is cheaper and less error-prone than carrying weights through every metric.
    """
    positions = (rng.random() + np.arange(n)) / n
    cumsum = np.cumsum(w)
    cumsum[-1] = 1.0
    return np.searchsorted(cumsum, positions)


@dataclass
class Posterior:
    """An equal-weight set of posterior particles and their trajectories.

    Produced either by importance sampling (fast, degenerate above a handful of
    dimensions) or by tempered SMC (what M0 actually uses). Both routes end in
    the same equal-weight representation so that everything downstream --
    quantiles, CRPS, PIT -- has one code path.
    """

    times: np.ndarray
    particle_paths: dict[str, np.ndarray]
    params: list[dict[str, Any]]
    ess: float
    n_unique: int
    method: str

    @property
    def n_particles(self) -> int:
        return len(self.params)

    def paths(self, series: str) -> np.ndarray:
        return self.particle_paths[series]

    def at(self, series: str, years: Sequence[float]) -> np.ndarray:
        idx = {float(t): i for i, t in enumerate(self.times)}
        return self.particle_paths[series][:, [idx[float(y)] for y in years]]

    def quantiles(self, series: str, qs: Sequence[float]) -> np.ndarray:
        return np.quantile(self.paths(series), qs, axis=0)

    @property
    def unique_fraction(self) -> float:
        return self.n_unique / self.n_particles if self.n_particles else 0.0

    @property
    def degenerate(self) -> bool:
        return self.unique_fraction < 0.05

    def health(self) -> str:
        msg = (
            f"{self.method}: {self.n_particles} particles, "
            f"{self.n_unique} unique ({self.unique_fraction:.0%}), "
            f"ESS {self.ess:.1f}"
        )
        if self.degenerate:
            msg += (
                "  -- WARNING: swarm degenerate; the fan understates "
                "uncertainty and must not be presented as a result."
            )
        return msg

    @classmethod
    def from_smc(cls, res) -> "Posterior":
        return cls(
            times=res.times,
            particle_paths=res.paths,
            params=res.params,
            ess=float(res.n_unique),
            n_unique=res.n_unique,
            method="tempered SMC",
        )

    @classmethod
    def from_importance(
        cls,
        ens: Ensemble,
        calibration_obs: Mapping[str, Any],
        snapshot: Snapshot,
        n_resample: int = 2000,
        seed: int = 0,
        structural: float = STRUCTURAL_SCALE,
    ) -> "Posterior":
        """Kept for comparison. Degenerates badly here -- see uncertainty/smc.py."""
        rng = np.random.default_rng(seed)
        lw = log_weights(ens, calibration_obs, snapshot, structural)
        w = normalise_weights(lw)
        idx = systematic_resample(w, n_resample, rng)
        return cls(
            times=ens.times,
            particle_paths={s: v[idx, :] for s, v in ens.paths.items()},
            params=[ens.params[i] for i in idx],
            ess=effective_sample_size(w),
            n_unique=int(len(np.unique(idx))),
            method="prior importance sampling",
        )
