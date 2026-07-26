"""Fan charts.

Two constraints from the design shape this module more than aesthetics do.

§9.3 / §15.3 forbid publishing a single "most likely" curve. The ensemble median
is still drawn, because MAPE is reported against it and hiding it would be worse,
but it is drawn faint and labelled as what it is -- a summary statistic of a
distribution, not a forecast. The visual weight belongs to the bands.

§5 requires every output to carry its credible horizon and to grey out beyond it.
Within a 1950-2020 backtest nothing exceeds its horizon, so the marker is drawn
but inert; the machinery is here so that the first time a run projects past 2035
the greying happens automatically rather than being remembered.

Each panel also prints its own skill verdict. A panel showing a model that loses
to a random walk says so on its face, where nobody can quote the picture without
also quoting the caveat.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from ..backtest.runner import BacktestReport  # noqa: E402

#: Credible horizon by series, from design §5. Years beyond this are greyed.
CREDIBLE_HORIZON: dict[str, float] = {
    "population_mn": 2080.0,
    "working_age_share_pct": 2070.0,
    "old_age_share_pct": 2070.0,
    "lowcarbon_share_pct": 2045.0,
    "gdp_bn2011ppp": 2035.0,
    "primary_energy_ej": 2050.0,
    "co2_emissions_gtco2": 2050.0,
    "co2_ppm": 2100.0,
}

PRETTY: dict[str, str] = {
    "population_mn": "World population (millions)",
    "gdp_bn2011ppp": "World GDP (bn 2011 int'l $, PPP)",
    "primary_energy_ej": "Primary energy (EJ/yr)",
    "co2_emissions_gtco2": "CO2 emissions (GtCO2/yr)",
    "co2_ppm": "Atmospheric CO2 (ppm)",
    "working_age_share_pct": "Working-age share, 15-64 (%)",
    "old_age_share_pct": "Old-age share, 65+ (%)",
    "lowcarbon_share_pct": "Low-carbon share of primary energy (%)",
}

BANDS = [(0.05, 0.95, 0.16), (0.10, 0.90, 0.22), (0.25, 0.75, 0.30)]


def _panel(ax, report: BacktestReport, name: str) -> None:
    post = report.posterior
    times = post.times
    paths = post.paths(name)
    calib0, calib1 = report.holdout.calib
    test0, test1 = report.holdout.test

    for lo, hi, alpha in BANDS:
        qlo, qhi = np.quantile(paths, [lo, hi], axis=0)
        ax.fill_between(
            times, qlo, qhi, alpha=alpha, color="#2b6cb0", linewidth=0,
            label=f"{round((hi - lo) * 100)}% band" if alpha == 0.16 else None,
        )

    med = np.median(paths, axis=0)
    ax.plot(
        times, med, color="#2b6cb0", lw=1.0, ls="--", alpha=0.75,
        label="ensemble median (not a point forecast)",
    )

    snap = report.holdout.snapshot.series(name)
    in_calib = snap.years <= calib1
    ax.plot(
        snap.years[in_calib], snap.values[in_calib], "o", ms=5,
        color="#1a202c", label="observed (calibration)",
    )
    ax.plot(
        snap.years[~in_calib], snap.values[~in_calib], "D", ms=5,
        mfc="none", mec="#c53030", mew=1.6, label="observed (held out)",
    )

    ax.axvspan(calib0, calib1, color="#000000", alpha=0.045, linewidth=0)
    ax.axvline(calib1, color="#c53030", lw=1.2, ls=":")
    ax.text(
        calib1, ax.get_ylim()[1], " freeze ", color="#c53030",
        fontsize=7, va="top", ha="left", rotation=90,
    )

    horizon = CREDIBLE_HORIZON.get(name)
    if horizon is not None and horizon < times[-1]:
        ax.axvspan(horizon, times[-1], color="#718096", alpha=0.28, linewidth=0)
        ax.text(
            horizon, ax.get_ylim()[1], " beyond credible horizon ",
            fontsize=7, va="top", ha="left", rotation=90, color="#4a5568",
        )

    sc = report.scores[name]
    ok = sc.beats_all_baselines
    bname, bscore = sc.best_baseline
    ax.set_title(PRETTY.get(name, name), fontsize=10, loc="left")
    ax.text(
        0.015, 0.965,
        ("SKILL " if ok else "NO SKILL ")
        + f"{sc.skill_vs_best:+.0%} vs {bname}",
        transform=ax.transAxes, fontsize=7.5, va="top",
        color="#22543d" if ok else "#742a2a",
        bbox=dict(
            boxstyle="round,pad=0.28",
            fc="#c6f6d5" if ok else "#fed7d7",
            ec="none", alpha=0.95,
        ),
    )
    ax.grid(alpha=0.18, lw=0.6)
    ax.tick_params(labelsize=8)
    ax.set_xlim(times[0], times[-1])


def fan_figure(report: BacktestReport, path: Path, title: str | None = None):
    names = list(report.scores)
    n = len(names)
    ncols = 2
    nrows = (n + 1 + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(12.5, 3.05 * nrows))
    axes = np.atleast_1d(axes).ravel()

    for ax, name in zip(axes, names):
        _panel(ax, report, name)

    # Final panel: the scoreboard, so the picture cannot be shown without it.
    ax = axes[len(names)]
    ax.axis("off")
    prof = report.holdout.snapshot.grade_profile(names)
    lines = [
        f"Hold-out: calibrate {report.holdout.calib[0]:.0f}-"
        f"{report.holdout.calib[1]:.0f}, score "
        f"{report.holdout.test[0]:.0f}-{report.holdout.test[1]:.0f}",
        f"Beat all baselines on {report.n_beaten}/{len(names)} series",
        f"{report.posterior.n_unique} unique particles of {report.posterior.n_particles}",
        f"Data grades: {prof.describe()}",
        "",
        prof.caveat(),
        "",
        "Bands are posterior predictive quantiles, not confidence in a path.",
        "Baselines carry fitted uncertainty; CRPS comparison is like-for-like.",
    ]
    ax.text(
        0.0, 0.98, "\n".join(lines), transform=ax.transAxes,
        fontsize=8.2, va="top", family="monospace", linespacing=1.55,
    )

    for ax in axes[len(names) + 1:]:
        ax.axis("off")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, labels, loc="lower center", ncol=5, fontsize=8,
        frameon=False, bbox_to_anchor=(0.5, -0.005),
    )
    fig.suptitle(
        title or "civsim M1 -- world aggregate backtest, posterior predictive",
        fontsize=12, x=0.008, ha="left",
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.975))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
