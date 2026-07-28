"""Forward projection chart.

Deliberately different from the backtest fan. A backtest panel can carry a skill
verdict because there is an observation to score against; a projection cannot,
and drawing it in the same style would invite it to be read the same way.

So every panel here states the model's *backtest* verdict for that variable
instead. A projection of a channel that loses to trend extrapolation is not
worthless -- the constraint and sensitivity statements still hold -- but it must
not be read as a forecast, and the only reliable place to say so is on the
picture itself.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .fan import CREDIBLE_HORIZON, PRETTY  # noqa: E402

BANDS = [(0.05, 0.95, 0.15), (0.25, 0.75, 0.28)]


def forward_figure(ens, series, path, verdicts=None, split_year=2020.0):
    verdicts = verdicts or {}
    n = len(series)
    nrows = (n + 1 + 1) // 2
    fig, axes = plt.subplots(nrows, 2, figsize=(12.5, 3.0 * nrows))
    axes = np.atleast_1d(axes).ravel()

    for ax, name in zip(axes, series):
        t, p = ens.times, ens.paths[name]
        for lo, hi, a in BANDS:
            qlo, qhi = np.quantile(p, [lo, hi], axis=0)
            ax.fill_between(t, qlo, qhi, alpha=a, color="#2b6cb0", linewidth=0,
                            label=f"{round((hi-lo)*100)}% band" if a == 0.15 else None)
        ax.plot(t, np.median(p, axis=0), color="#2b6cb0", lw=1.0, ls="--",
                alpha=0.7, label="median (not a forecast)")
        ax.axvline(split_year, color="#1a202c", lw=1.0, ls=":")
        ax.text(split_year, ax.get_ylim()[1], " calibrated | projected ",
                fontsize=7, va="top", ha="left", rotation=90, color="#1a202c")

        h = CREDIBLE_HORIZON.get(name)
        if h is not None and h < t[-1]:
            ax.axvspan(h, t[-1], color="#718096", alpha=0.30, linewidth=0)
            ax.text(h, ax.get_ylim()[1], " beyond credible horizon ", fontsize=7,
                    va="top", ha="left", rotation=90, color="#4a5568")

        v = verdicts.get(name, "no backtest verdict")
        ok = v.startswith("ROBUST SKILL")
        ax.text(0.015, 0.96, f"backtest: {v}", transform=ax.transAxes,
                fontsize=7.5, va="top", color="#22543d" if ok else "#742a2a",
                bbox=dict(boxstyle="round,pad=0.28",
                          fc="#c6f6d5" if ok else "#fed7d7", ec="none", alpha=0.95))
        ax.set_title(PRETTY.get(name, name), fontsize=10, loc="left")
        ax.grid(alpha=0.18, lw=0.6)
        ax.tick_params(labelsize=8)
        ax.set_xlim(t[0], t[-1])

    ax = axes[len(series)]
    ax.axis("off")
    lines = [
        f"{ens.n_feasible}/{ens.n_requested} trajectories feasible",
        f"{len(ens.exclusions)} excluded by a physical limit "
        f"({ens.exclusion_rate:.0%})",
        "",
        "THIS IS NOT A FORECAST.",
        "The model has robust backtest skill on 1 of 13 series.",
        "",
        "What survives that: statements about which futures the",
        "constraint structure rules out, and which parameters drive",
        "the spread. Neither needs the model to forecast well.",
        "",
        "An exclusion means 'unreachable for the reasons this model",
        "tracks' -- weaker than 'impossible', and the strongest claim",
        "an aggregate model can honestly make.",
    ]
    ax.text(0.0, 0.98, "\n".join(lines), transform=ax.transAxes, fontsize=8.2,
            va="top", family="monospace", linespacing=1.5)
    for a in axes[len(series) + 1:]:
        a.axis("off")

    hs, ls = axes[0].get_legend_handles_labels()
    fig.legend(hs, ls, loc="lower center", ncol=4, fontsize=8, frameon=False,
               bbox_to_anchor=(0.5, -0.005))
    fig.suptitle("civsim M4 -- projection to 2100, constraint and sensitivity",
                 fontsize=12, x=0.008, ha="left")
    fig.tight_layout(rect=(0, 0.035, 1, 0.975))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
