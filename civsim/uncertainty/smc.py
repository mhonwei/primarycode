"""Tempered sequential Monte Carlo.

Importance sampling straight from the prior does not work here and no amount of
raising the draw count fixes it. With ~24 free parameters and a likelihood sharp
enough to be worth conditioning on, the weight distribution is dominated by a
single particle: measured on this model, the best draw out of 4000 beats the
second best by 13 nats, so the effective sample size is 1.0 and the "posterior
predictive fan" is one trajectory drawn four thousand times. It looks like a
confident result and is an empty one.

Tempered SMC walks from prior to posterior through a sequence of intermediate
distributions p_k proportional to prior x likelihood^beta_k, with
0 = beta_0 < ... < beta_K = 1. Each step is small enough that reweighting stays
well conditioned; after each reweight the particles are resampled and then moved
by a random-walk Metropolis kernel that leaves p_k invariant, which restores
diversity that resampling destroyed. The cost is one model re-run per particle
per move.

The schedule is adaptive: beta_next is found by bisection so that the ESS after
reweighting hits a target fraction of N. This spends steps where the geometry is
hard instead of on a fixed grid chosen in advance.

Diagnostics worth watching in the returned object:
  ess_history      should stay near the target; a collapse means the schedule
                   is advancing too fast.
  accept_history   0.15-0.4 is healthy. Near zero means the proposal is too
                   wide; near one means it is too narrow and the particles are
                   not actually moving.
  n_unique         unique particles at beta=1. If this is small, the run is
                   still degenerate and the fan is still too narrow -- report it
                   rather than presenting the chart.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from ..core.financial import SectorBalanceViolation
from ..core.ledger import ConservationViolation
from ..data.registry import Snapshot
from ..model import OBSERVED_SERIES, build_engine
from .priors import (
    M0_PRIOR,
    Dist,
    free_names,
    log_prior,
    params_to_vector,
    prior_scales,
    vector_to_params,
)


def simulate_aligned(
    param_sets: Sequence[Mapping[str, Any]],
    snapshot: Snapshot,
    t0: float,
    t1: float,
    series: Sequence[str] = OBSERVED_SERIES,
) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray]:
    """Run every parameter set, preserving order.

    Unlike :func:`~civsim.uncertainty.sampler.run_ensemble`, failed members are
    kept as NaN rows rather than dropped: SMC needs particle index alignment,
    and a failed proposal must be rejected, not silently removed from the swarm.

    Returns (times, paths, ok_mask).
    """
    n = len(param_sets)
    n_t = int(round(t1 - t0)) + 1
    times = np.arange(t0, t0 + n_t, 1.0)
    paths = {s: np.full((n, n_t), np.nan) for s in series}
    ok = np.zeros(n, dtype=bool)

    for i, p in enumerate(param_sets):
        try:
            eng = build_engine(p, snapshot, t0=t0, check_conservation=True)
            traj = eng.run(t0, t1)
        except (ConservationViolation, SectorBalanceViolation):
            raise  # model bug, never a bad draw
        except (ValueError, ArithmeticError, RuntimeError, KeyError):
            continue
        vals = {s: traj.series(s) for s in series}
        if any(not np.all(np.isfinite(v)) for v in vals.values()):
            continue
        if any(np.any(v <= 0) for v in vals.values()):
            continue
        for s in series:
            paths[s][i, :] = vals[s]
        ok[i] = True

    return times, paths, ok


@dataclass
class SMCResult:
    times: np.ndarray
    paths: dict[str, np.ndarray]
    params: list[dict[str, Any]]
    loglik: np.ndarray
    beta_history: list[float] = field(default_factory=list)
    ess_history: list[float] = field(default_factory=list)
    accept_history: list[float] = field(default_factory=list)
    n_model_runs: int = 0

    @property
    def n_particles(self) -> int:
        return len(self.params)

    @property
    def n_unique(self) -> int:
        v = np.array([params_to_vector(p) for p in self.params])
        return int(len(np.unique(np.round(v, 12), axis=0)))

    def health(self) -> str:
        frac = self.n_unique / self.n_particles if self.n_particles else 0.0
        msg = (
            f"{self.n_particles} particles, {self.n_unique} unique "
            f"({frac:.0%}); {len(self.beta_history) - 1} tempering steps; "
            f"{self.n_model_runs} model runs; "
            f"accept {np.mean(self.accept_history or [0]):.0%}"
        )
        if frac < 0.05:
            msg += (
                "  -- WARNING: swarm is degenerate. The fan understates "
                "uncertainty; do not present it."
            )
        return msg


def _ess_at(loglik: np.ndarray, base: np.ndarray, beta_delta: float) -> float:
    lw = base + beta_delta * loglik
    lw = np.where(np.isfinite(lw), lw, -np.inf)
    if not np.any(np.isfinite(lw)):
        return 0.0
    w = np.exp(lw - lw[np.isfinite(lw)].max())
    w[~np.isfinite(w)] = 0.0
    s = w.sum()
    if s <= 0:
        return 0.0
    w = w / s
    return float(1.0 / np.sum(w**2))


def _next_beta(
    loglik: np.ndarray, beta: float, target_ess: float, tol: float = 1e-6
) -> float:
    """Bisect for the largest step whose reweighting keeps ESS at target."""
    zero = np.zeros_like(loglik)
    if _ess_at(loglik, zero, 1.0 - beta) >= target_ess:
        return 1.0
    lo, hi = 0.0, 1.0 - beta
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if _ess_at(loglik, zero, mid) >= target_ess:
            lo = mid
        else:
            hi = mid
    return beta + max(lo, tol)


def _systematic(w: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    pos = (rng.random() + np.arange(n)) / n
    c = np.cumsum(w)
    c[-1] = 1.0
    return np.searchsorted(c, pos)


def run_smc(
    loglik_fn: Callable[[dict[str, np.ndarray], np.ndarray, np.ndarray], np.ndarray],
    snapshot: Snapshot,
    t0: float,
    t1: float,
    n_particles: int = 1500,
    seed: int = 0,
    prior: Mapping[str, Dist] | None = None,
    series: Sequence[str] = OBSERVED_SERIES,
    ess_target_frac: float = 0.5,
    n_moves: int = 2,
    max_stages: int = 40,
    verbose: bool = True,
) -> SMCResult:
    """Walk from prior to posterior by adaptive tempering.

    `loglik_fn(paths, times, ok_mask) -> loglik array` must depend only on
    calibration-window data. The hold-out discipline is enforced by what the
    caller closes over, and this function never sees observations directly.
    """
    from .priors import sample_prior

    p = dict(prior or M0_PRIOR)
    names = free_names(p)
    rng = np.random.default_rng(seed)
    target = ess_target_frac * n_particles

    params = sample_prior(rng, n_particles, p)
    times, paths, ok = simulate_aligned(params, snapshot, t0, t1, series)
    runs = n_particles
    ll = loglik_fn(paths, times, ok)
    ll = np.where(ok, ll, -np.inf)

    beta = 0.0
    res = SMCResult(times, paths, params, ll, [0.0], [float(n_particles)], [], runs)

    scales = prior_scales(p)
    stage = 0
    while beta < 1.0 and stage < max_stages:
        stage += 1
        new_beta = _next_beta(ll, beta, target)
        d_beta = new_beta - beta

        lw = d_beta * ll
        lw = np.where(np.isfinite(lw), lw, -np.inf)
        m = lw[np.isfinite(lw)].max()
        w = np.exp(lw - m)
        w[~np.isfinite(w)] = 0.0
        tot = w.sum()
        if tot <= 0:
            raise RuntimeError(
                f"SMC stalled at beta={beta:.4g}: every particle has zero "
                "weight. The model cannot reach the calibration data from "
                "anywhere in the prior."
            )
        w /= tot
        ess = float(1.0 / np.sum(w**2))

        idx = _systematic(w, n_particles, rng)
        params = [dict(params[i]) for i in idx]
        for s in series:
            paths[s] = paths[s][idx]
        ll = ll[idx]
        beta = new_beta

        # --- Metropolis moves at the new temperature ----------------------
        X = np.array([params_to_vector(q, p) for q in params])
        cov = np.cov(X.T) + np.diag((0.02 * scales) ** 2)
        try:
            L = np.linalg.cholesky(cov)
        except np.linalg.LinAlgError:
            L = np.diag(0.1 * scales)
        step = 2.38 / np.sqrt(max(len(names), 1))

        accepts = []
        for _ in range(n_moves):
            Z = rng.normal(size=X.shape)
            Xp = X + step * Z @ L.T
            prop = [vector_to_params(Xp[i], params[i], p) for i in range(n_particles)]
            lp_old = np.array([log_prior(q, p) for q in params])
            lp_new = np.array([log_prior(q, p) for q in prop])

            live = np.isfinite(lp_new)
            t_paths = {s: np.full_like(paths[s], np.nan) for s in series}
            ll_new = np.full(n_particles, -np.inf)
            if live.any():
                sub = [prop[i] for i in np.flatnonzero(live)]
                _, sub_paths, sub_ok = simulate_aligned(sub, snapshot, t0, t1, series)
                runs += len(sub)
                sub_ll = loglik_fn(sub_paths, times, sub_ok)
                sub_ll = np.where(sub_ok, sub_ll, -np.inf)
                for j, i in enumerate(np.flatnonzero(live)):
                    ll_new[i] = sub_ll[j]
                    for s in series:
                        t_paths[s][i] = sub_paths[s][j]

            log_alpha = (lp_new + beta * ll_new) - (lp_old + beta * ll)
            log_alpha = np.where(np.isfinite(log_alpha), log_alpha, -np.inf)
            acc = np.log(rng.random(n_particles)) < log_alpha
            accepts.append(float(acc.mean()))

            for i in np.flatnonzero(acc):
                params[i] = prop[i]
                ll[i] = ll_new[i]
                for s in series:
                    paths[s][i] = t_paths[s][i]
            X = np.array([params_to_vector(q, p) for q in params])

        res.beta_history.append(beta)
        res.ess_history.append(ess)
        res.accept_history.append(float(np.mean(accepts)))
        if verbose:
            print(
                f"  smc stage {stage:2d}  beta={beta:.4f}  ess={ess:7.1f}  "
                f"accept={np.mean(accepts):.0%}  unique={len(np.unique(np.round(X, 12), axis=0)):4d}"
            )

    res.params = params
    res.paths = paths
    res.loglik = ll
    res.n_model_runs = runs
    if beta < 1.0:
        raise RuntimeError(
            f"SMC did not reach beta=1 in {max_stages} stages (got {beta:.4g})."
        )
    return res
