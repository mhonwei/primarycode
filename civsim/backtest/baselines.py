"""Naive baselines -- the bar the model has to clear (§11.2).

A simulator that cannot beat a random walk on a variable has, for that variable,
added nothing but machinery. The design commits to reporting that outcome rather
than burying it, which only works if the baselines are computed by the same code
path and scored by the same metric as the model.

Each baseline fits on the calibration window and emits an *ensemble* over the
test years, not a point forecast. That matters: comparing a probabilistic model
against a point baseline on a proper score is rigged in the model's favour,
because the point forecast is penalised for a sharpness it never claimed. Every
baseline here carries its own fitted uncertainty, estimated from calibration
residuals, so CRPS comparisons are like-for-like.

All baselines work in log space. These are positive, multiplicatively growing
series; a linear-space random walk on world GDP will happily emit negative
output and then look artificially bad.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class BaselineForecast:
    name: str
    years: np.ndarray
    #: (n_members, n_years)
    ensemble: np.ndarray

    @property
    def median(self) -> np.ndarray:
        return np.median(self.ensemble, axis=0)


class Baseline:
    name = "baseline"

    def forecast(
        self,
        years_in: np.ndarray,
        values_in: np.ndarray,
        years_out: np.ndarray,
        rng: np.random.Generator,
        n: int = 1000,
    ) -> BaselineForecast:
        raise NotImplementedError


def _log(v: np.ndarray) -> np.ndarray:
    if np.any(v <= 0):
        raise ValueError("baselines assume strictly positive series")
    return np.log(v)


class RandomWalk(Baseline):
    """Last value persists; uncertainty grows as sqrt(horizon).

    The standard hard-to-beat benchmark for macro series.
    """

    name = "random_walk"

    def forecast(self, years_in, values_in, years_out, rng, n=1000):
        lv = _log(values_in)
        steps = np.diff(lv)
        dt_in = np.diff(years_in)
        drift_sd = float(np.std(steps / np.sqrt(dt_in), ddof=1))
        last_y, last_v = years_in[-1], lv[-1]
        h = years_out - last_y
        shocks = rng.normal(0.0, 1.0, size=(n, len(years_out)))
        paths = last_v + shocks * drift_sd * np.sqrt(h)[None, :]
        return BaselineForecast(self.name, years_out, np.exp(paths))


class DriftingRandomWalk(Baseline):
    """Random walk with the calibration-average drift carried forward."""

    name = "random_walk_drift"

    def forecast(self, years_in, values_in, years_out, rng, n=1000):
        lv = _log(values_in)
        dt_in = np.diff(years_in)
        rates = np.diff(lv) / dt_in
        mu = float(np.mean(rates))
        sd = float(np.std(rates, ddof=1))
        last_y, last_v = years_in[-1], lv[-1]
        h = years_out - last_y
        # Uncertainty compounds with horizon and includes drift uncertainty.
        drift_draw = rng.normal(mu, sd / np.sqrt(len(rates)), size=(n, 1))
        diffusion = rng.normal(0.0, 1.0, size=(n, len(years_out))) * sd * np.sqrt(h)
        paths = last_v + drift_draw * h[None, :] + diffusion
        return BaselineForecast(self.name, years_out, np.exp(paths))


class LogLinearTrend(Baseline):
    """OLS on log value against year, with residual-based predictive spread."""

    name = "loglinear_trend"

    def forecast(self, years_in, values_in, years_out, rng, n=1000):
        lv = _log(values_in)
        A = np.vstack([years_in, np.ones_like(years_in)]).T
        coef, *_ = np.linalg.lstsq(A, lv, rcond=None)
        resid = lv - A @ coef
        dof = max(len(lv) - 2, 1)
        sd = float(np.sqrt(np.sum(resid**2) / dof))
        mean_out = coef[0] * years_out + coef[1]
        # Extrapolation variance grows with distance from the fit centroid.
        xbar = float(np.mean(years_in))
        sxx = float(np.sum((years_in - xbar) ** 2))
        se = sd * np.sqrt(1.0 + 1.0 / len(lv) + (years_out - xbar) ** 2 / sxx)
        draws = rng.normal(0.0, 1.0, size=(n, len(years_out))) * se[None, :]
        return BaselineForecast(self.name, years_out, np.exp(mean_out + draws))


class AR1OnGrowth(Baseline):
    """AR(1) on log growth rates, simulated forward on the observation grid."""

    name = "ar1_growth"

    def forecast(self, years_in, values_in, years_out, rng, n=1000):
        lv = _log(values_in)
        dt_in = np.diff(years_in)
        g = np.diff(lv) / dt_in
        mu = float(np.mean(g))
        dev = g - mu
        if len(dev) > 2 and np.sum(dev[:-1] ** 2) > 0:
            phi = float(np.sum(dev[:-1] * dev[1:]) / np.sum(dev[:-1] ** 2))
            phi = float(np.clip(phi, -0.95, 0.95))
        else:
            phi = 0.0
        eps_sd = float(np.std(dev[1:] - phi * dev[:-1], ddof=1)) if len(dev) > 2 else float(np.std(dev, ddof=1))

        last_y, last_v = years_in[-1], lv[-1]
        grid = np.concatenate([[last_y], years_out])
        out = np.empty((n, len(years_out)))
        state = np.full(n, dev[-1])
        level = np.full(n, last_v)
        for j in range(len(years_out)):
            span = grid[j + 1] - grid[j]
            for _ in range(int(round(span))):
                state = phi * state + rng.normal(0.0, eps_sd, n)
                level = level + (mu + state)
            out[:, j] = level
        return BaselineForecast(self.name, years_out, np.exp(out))


class RecentTrend(Baseline):
    """'Last 20 years of growth continues' -- the forecast a sensible
    non-modeller would make, and the one §11.2 names explicitly."""

    name = "recent_trend"

    def __init__(self, window_years: float = 20.0) -> None:
        self.window_years = window_years

    def forecast(self, years_in, values_in, years_out, rng, n=1000):
        m = years_in >= (years_in[-1] - self.window_years)
        yi, vi = years_in[m], values_in[m]
        lv = _log(vi)
        rate = (lv[-1] - lv[0]) / (yi[-1] - yi[0])
        rates = np.diff(lv) / np.diff(yi)
        sd = float(np.std(rates, ddof=1)) if len(rates) > 1 else 0.01
        h = years_out - years_in[-1]
        drift = rng.normal(rate, sd / np.sqrt(max(len(rates), 1)), size=(n, 1))
        noise = rng.normal(0.0, 1.0, size=(n, len(years_out))) * sd * np.sqrt(h)
        paths = _log(values_in)[-1] + drift * h[None, :] + noise
        return BaselineForecast(self.name, years_out, np.exp(paths))


DEFAULT_BASELINES: list[Baseline] = [
    RandomWalk(),
    DriftingRandomWalk(),
    LogLinearTrend(),
    AR1OnGrowth(),
    RecentTrend(),
]
