"""End-to-end backtest: prior -> calibration -> freeze -> reveal -> score.

The order of operations in :func:`run_backtest` is the protocol. It is written
as one linear function, rather than spread across helpers, so that a reader can
confirm in thirty seconds that the test window is revealed *after* the posterior
is frozen and is never passed to anything that fits.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from ..data.registry import Snapshot
from ..model import OBSERVED_SERIES
from ..uncertainty.priors import M0_PRIOR, describe_prior, free_names
from ..uncertainty.sampler import (
    DISCREPANCY_CORR_YEARS,
    Posterior,
    STRUCTURAL_SCALE,
    effective_n_obs,
    loglik_paths,
)
from ..uncertainty.smc import SMCResult, run_smc
from .baselines import DEFAULT_BASELINES, Baseline
from .protocol import Holdout
from .scoring import SeriesScore, crps_series, pit_uniformity, pit_values


@dataclass
class BacktestReport:
    holdout: Holdout
    posterior: Posterior
    smc: SMCResult
    scores: dict[str, SeriesScore]
    n_draws: int
    seed: int
    structural_scale: float
    baseline_names: list[str] = field(default_factory=list)

    def summary_table(self) -> str:
        w = 22
        lines = [
            f"{'series':<{w}} {'CRPS(model)':>12} {'CRPS(best base)':>16} "
            f"{'baseline':>18} {'skill':>8} {'MAPE':>7} {'PIT chi2':>9}",
            "-" * (w + 76),
        ]
        for name, sc in self.scores.items():
            bname, bscore = sc.best_baseline
            lines.append(
                f"{name:<{w}} {sc.model_crps_mean:>12.4g} {bscore:>16.4g} "
                f"{bname:>18} {sc.skill_vs_best:>+7.1%} "
                f"{sc.model_mape:>6.1f}% {pit_uniformity(sc.pit):>9.2f}"
            )
        return "\n".join(lines)

    def verdicts(self) -> str:
        return "\n".join(
            f"  {n}: {s.verdict()}" for n, s in self.scores.items()
        )

    @property
    def n_beaten(self) -> int:
        return sum(1 for s in self.scores.values() if s.beats_all_baselines)

    def manifest(self) -> dict[str, Any]:
        return {
            "protocol": self.holdout.manifest(),
            "sampler": {
                "method": self.posterior.method,
                "n_particles": self.posterior.n_particles,
                "n_unique": self.posterior.n_unique,
                "unique_fraction": self.posterior.unique_fraction,
                "degenerate": bool(self.posterior.degenerate),
                "n_model_runs": self.smc.n_model_runs,
                "tempering_steps": len(self.smc.beta_history) - 1,
                "beta_history": [float(b) for b in self.smc.beta_history],
                "ess_history": [float(e) for e in self.smc.ess_history],
                "accept_history": [float(a) for a in self.smc.accept_history],
            },
            "seed": self.seed,
            "structural_likelihood_scale": self.structural_scale,
            "discrepancy_corr_years": DISCREPANCY_CORR_YEARS,
            "baselines": self.baseline_names,
            "scores": {
                n: {
                    "model_crps": s.model_crps_mean,
                    "baseline_crps": s.baseline_crps_mean,
                    "best_baseline": s.best_baseline[0],
                    "skill_vs_best": s.skill_vs_best,
                    "beats_all_baselines": bool(s.beats_all_baselines),
                    "model_mape_pct": s.model_mape,
                    "pit_chi2": pit_uniformity(s.pit),
                    "scored_years": [float(y) for y in s.years],
                }
                for n, s in self.scores.items()
            },
        }

    def write_manifest(self, path: Path) -> None:
        Path(path).write_text(json.dumps(self.manifest(), indent=2) + "\n")


def run_backtest(
    snapshot: Snapshot | None = None,
    calib: tuple[float, float] = (1950.0, 1990.0),
    test: tuple[float, float] = (1990.0, 2020.0),
    series: Sequence[str] = OBSERVED_SERIES,
    n_draws: int = 4000,
    n_resample: int = 2000,
    seed: int = 20260726,
    structural_scale: float = STRUCTURAL_SCALE,
    baselines: Sequence[Baseline] | None = None,
    verbose: bool = True,
) -> BacktestReport:
    snap = snapshot or Snapshot()
    rng = np.random.default_rng(seed)
    bl = list(baselines or DEFAULT_BASELINES)

    holdout = Holdout(snapshot=snap, calib=calib, test=test, series=tuple(series))

    def say(msg: str) -> None:
        if verbose:
            print(msg)

    say(f"snapshot   {snap.path.name}  sha256={snap.sha256[:16]}...")
    say(f"protocol   calibrate {calib[0]:.0f}-{calib[1]:.0f}, "
        f"score {test[0]:.0f}-{test[1]:.0f} (disjoint)")

    # 1. Calibration data. This is the ONLY observation set the sampler sees.
    holdout.assert_fit_allowed()
    calib_obs = holdout.calibration()
    n_eff = effective_n_obs(calib_obs[series[0]].years)
    say(f"prior      {len(free_names())} free parameters "
        f"({len(M0_PRIOR)} total)")
    say(f"likelihood {len(calib_obs[series[0]].years)} calibration years worth "
        f"{n_eff:.2f} independent observations at "
        f"{DISCREPANCY_CORR_YEARS:.0f}y discrepancy correlation")

    def loglik_fn(paths, times, ok):
        return loglik_paths(
            paths, times, calib_obs, snap,
            structural=structural_scale,
        )

    # 2. Tempered SMC from prior to posterior ------------------------------
    say(f"smc        {n_draws} particles, prior -> posterior")
    smc = run_smc(
        loglik_fn, snap, t0=calib[0], t1=test[1],
        n_particles=n_draws, seed=seed, series=series, verbose=verbose,
    )
    post = Posterior.from_smc(smc)
    say(f"posterior  {post.health()}")

    # 4. Freeze -- nothing may be fitted past this line ---------------------
    holdout.freeze(
        note="M0 tempered-SMC fit; structure and priors frozen before reveal.",
        extra={
            "n_particles": n_draws,
            "n_unique": post.n_unique,
            "sampler": post.method,
            "structural_scale": structural_scale,
            "discrepancy_corr_years": DISCREPANCY_CORR_YEARS,
        },
    )
    say("freeze     posterior locked; test window now readable")

    # 5. Reveal test window -------------------------------------------------
    test_obs = holdout.reveal_test()
    score_years = holdout.scoring_years()
    say(f"reveal     scoring on {len(score_years)} observed grid years: "
        f"{[int(y) for y in score_years]}")

    # 6. Score model and baselines like-for-like ---------------------------
    scores: dict[str, SeriesScore] = {}
    for name in series:
        obs = test_obs[name]
        model_ens = post.at(name, obs.years)
        m_crps = crps_series(model_ens, obs.values)

        c_in = calib_obs[name]
        b_crps: dict[str, np.ndarray] = {}
        for b in bl:
            fc = b.forecast(
                c_in.years, c_in.values, obs.years,
                np.random.default_rng(seed + hash(b.name) % 10_000),
                n=n_resample,
            )
            b_crps[b.name] = crps_series(fc.ensemble, obs.values)

        scores[name] = SeriesScore(
            series=name,
            years=obs.years,
            observed=obs.values,
            model_crps=m_crps,
            model_median=np.median(model_ens, axis=0),
            baseline_crps=b_crps,
            pit=pit_values(model_ens, obs.values),
        )

    return BacktestReport(
        holdout=holdout,
        posterior=post,
        smc=smc,
        scores=scores,
        n_draws=n_draws,
        seed=seed,
        structural_scale=structural_scale,
        baseline_names=[b.name for b in bl],
    )


def prior_report() -> str:
    return "M0 prior:\n" + describe_prior()
