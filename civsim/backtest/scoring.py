"""Proper scoring for ensemble forecasts (§11.2).

CRPS is the primary metric. It is a *proper* score, so a forecaster minimises it
by reporting its honest predictive distribution rather than by being vague; and
it reduces to absolute error for a point forecast, so model and baseline sit on
one scale. Comparing an ensemble to a point forecast by RMSE-of-the-median, the
obvious shortcut, rewards overconfidence -- exactly the failure a project built
around uncertainty quantification must not reward.

Skill is reported relative to the *best* baseline, not a convenient one. Beating
a random walk while losing to a log-linear trend is not skill, and §11.2 says so
in as many words.

PIT histograms are included because they catch what CRPS averages away: a model
can post a decent CRPS while being systematically overconfident. If the PIT
values are not roughly uniform, the fan chart's width is wrong even when its
centre is right.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def crps_ensemble(ensemble: np.ndarray, observed: float) -> float:
    """CRPS of an equally-weighted ensemble against a scalar observation.

    Uses the O(n log n) identity
        CRPS = mean|X - y| - 0.5 * mean|X - X'|
    with the second term evaluated from the sorted sample.
    """
    x = np.sort(np.asarray(ensemble, dtype=float))
    n = x.size
    if n == 0:
        return float("nan")
    term1 = float(np.mean(np.abs(x - observed)))
    # sum_ij |xi - xj| = 2 * sum_i (2i - n + 1) x_i  for sorted x, i from 0
    i = np.arange(n)
    gini = float(np.sum((2 * i - n + 1) * x))
    term2 = gini / (n * n)
    return term1 - term2


def crps_series(ensemble: np.ndarray, observed: np.ndarray) -> np.ndarray:
    """CRPS per time point. ensemble is (n_members, n_times)."""
    return np.array(
        [crps_ensemble(ensemble[:, j], float(observed[j]))
         for j in range(ensemble.shape[1])]
    )


def pit_values(ensemble: np.ndarray, observed: np.ndarray) -> np.ndarray:
    """Probability integral transform: F(y) under the empirical ensemble CDF."""
    out = np.empty(ensemble.shape[1])
    for j in range(ensemble.shape[1]):
        out[j] = float(np.mean(ensemble[:, j] <= observed[j]))
    return out


def mae(pred: np.ndarray, observed: np.ndarray) -> float:
    return float(np.mean(np.abs(pred - observed)))


def mape(pred: np.ndarray, observed: np.ndarray) -> float:
    return float(np.mean(np.abs((pred - observed) / observed))) * 100.0


def skill_score(score_model: float, score_reference: float) -> float:
    """1 - model/reference. Positive means the model is better.

    Undefined when the reference is perfect; returns nan rather than inf so it
    cannot silently propagate into a summary table as a spurious win.
    """
    if score_reference <= 0 or not np.isfinite(score_reference):
        return float("nan")
    return 1.0 - score_model / score_reference


@dataclass
class SeriesScore:
    series: str
    years: np.ndarray
    observed: np.ndarray
    model_crps: np.ndarray
    model_median: np.ndarray
    baseline_crps: dict[str, np.ndarray]
    pit: np.ndarray

    @property
    def model_crps_mean(self) -> float:
        return float(np.mean(self.model_crps))

    @property
    def baseline_crps_mean(self) -> dict[str, float]:
        return {k: float(np.mean(v)) for k, v in self.baseline_crps.items()}

    @property
    def best_baseline(self) -> tuple[str, float]:
        d = self.baseline_crps_mean
        name = min(d, key=lambda k: d[k])
        return name, d[name]

    @property
    def skill_vs_best(self) -> float:
        _, s = self.best_baseline
        return skill_score(self.model_crps_mean, s)

    @property
    def beats_all_baselines(self) -> bool:
        return self.skill_vs_best > 0

    @property
    def model_mape(self) -> float:
        return mape(self.model_median, self.observed)

    def verdict(self) -> str:
        """The sentence §11.2 requires us to print whether we like it or not."""
        name, s = self.best_baseline
        if self.skill_vs_best > 0:
            return (
                f"BEATS baselines: CRPS {self.model_crps_mean:.4g} vs "
                f"{s:.4g} ({name}), skill {self.skill_vs_best:+.1%}"
            )
        return (
            f"NO SKILL: CRPS {self.model_crps_mean:.4g} vs {s:.4g} ({name}), "
            f"skill {self.skill_vs_best:+.1%} -- the model adds nothing over "
            f"{name} for this variable and must not be quoted as if it did"
        )


def pit_uniformity(pit: np.ndarray, n_bins: int = 4) -> float:
    """Chi-square statistic against uniform. Large means miscalibrated width."""
    if pit.size == 0:
        return float("nan")
    counts, _ = np.histogram(pit, bins=n_bins, range=(0.0, 1.0))
    expected = pit.size / n_bins
    return float(np.sum((counts - expected) ** 2) / expected)
