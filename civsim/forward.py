"""Forward projection, exclusion analysis, and path archetypes.

This is the first module in the project that produces what design §7 says the
product actually is. Four milestones built backtest machinery; the deliverables
§7 names are:

  (a) probability fans                      -- existed since M0
  (b) the set of paths ruled out by constraint  -- did not exist
  (c) bifurcation and sensitivity maps      -- did not exist
  (d) an audit trail                        -- existed since M0

(b) and (c) are built here, and the reason they matter is that **neither
requires predictive skill.** The model has robust skill on 1 of 13 series. It
cannot tell you what 2100 looks like and this module does not pretend to. What
it can do is say which futures are unreachable without violating conservation,
and where in parameter space trajectories separate — and those are statements
about the constraint structure, not about the forecast.

Exclusion is the sharper of the two
-----------------------------------
Every parameter draw that fails to integrate is a *result*: it names a future
the model rules out and the stock whose exhaustion rules it out. Until M4 those
draws were discarded as noise. They were the one output that did not depend on
the model forecasting anything well.

This only works because :class:`~civsim.core.stocks.Limit` now separates a real
reserve from a bookkeeping pool. Before that separation, sweeping 120 forward
runs produced 33 exclusions from an accounting reservoir I had sized by guess
and 13 from the fossil carbon reserve; reported together they would have looked
like one finding about the world, and three quarters of it would have been a
statement about my own arbitrary constant.

What an exclusion is and is not
-------------------------------
An exclusion is conditional on the model's structure, so it is not "this future
cannot happen". It is "this future cannot happen *for the reasons this model
tracks*" -- which is weaker, but is falsifiable and is the strongest thing an
aggregate model can honestly claim.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .core.engine import ConstraintBinding, ReservoirUndersized
from .data.registry import Snapshot
from .model import OBSERVED_SERIES, build_engine
from .uncertainty.priors import M0_PRIOR, free_names


@dataclass
class Exclusion:
    """One trajectory the constraint structure rules out."""

    draw: int
    stock: str
    year: float
    params: dict[str, Any]


@dataclass
class ForwardEnsemble:
    times: np.ndarray
    paths: dict[str, np.ndarray]
    params: list[dict[str, Any]]
    exclusions: list[Exclusion] = field(default_factory=list)
    other_failures: Counter = field(default_factory=Counter)
    n_requested: int = 0

    @property
    def n_feasible(self) -> int:
        return len(self.params)

    @property
    def exclusion_rate(self) -> float:
        return len(self.exclusions) / self.n_requested if self.n_requested else 0.0

    def binding_constraints(self) -> Counter:
        return Counter(e.stock for e in self.exclusions)

    def binding_years(self, stock: str) -> np.ndarray:
        return np.array([e.year for e in self.exclusions if e.stock == stock])

    def at(self, series: str, year: float) -> np.ndarray:
        i = int(np.argmin(np.abs(self.times - year)))
        return self.paths[series][:, i]

    # ------------------------------------------------------------ reporting

    def exclusion_report(self) -> str:
        if not self.n_requested:
            return "no draws"
        lines = [
            f"{self.n_feasible}/{self.n_requested} trajectories feasible; "
            f"{len(self.exclusions)} excluded by a physical limit "
            f"({self.exclusion_rate:.0%})",
        ]
        if self.other_failures:
            lines.append(f"  other integration failures: {dict(self.other_failures)}")
        if not self.exclusions:
            lines.append("  no physical limit bound -- nothing is being ruled out")
            return "\n".join(lines)
        lines.append("")
        lines.append("  binding constraint                 draws   median year")
        lines.append("  " + "-" * 54)
        for stock, n in self.binding_constraints().most_common():
            yrs = self.binding_years(stock)
            lines.append(
                f"  {stock:<32} {n:>5}   {int(np.median(yrs))}"
                f"  [{int(yrs.min())}-{int(yrs.max())}]"
            )
        return "\n".join(lines)

    def feasibility_of(
        self, series: str, year: float, threshold: float, above: bool = True
    ) -> tuple[float, str]:
        """Fraction of *all* draws reaching a target, and how the rest failed.

        Excluded draws count in the denominator. A target that only the
        infeasible trajectories reach has a feasibility of zero, which is the
        whole point -- reporting it over survivors alone would silently discard
        the constraint.
        """
        v = self.at(series, year)
        hit = (v >= threshold) if above else (v <= threshold)
        frac = float(hit.sum()) / self.n_requested if self.n_requested else 0.0
        direction = "at least" if above else "at most"
        return frac, (
            f"{series} {direction} {threshold:g} in {int(year)}: "
            f"{frac:.1%} of all draws "
            f"({int(hit.sum())}/{self.n_requested}; "
            f"{len(self.exclusions)} of the rest were physically excluded)"
        )


def project(
    param_sets: Sequence[Mapping[str, Any]],
    snapshot: Snapshot | None = None,
    t0: float = 1950.0,
    t1: float = 2100.0,
    series: Sequence[str] = OBSERVED_SERIES,
    verbose: bool = False,
) -> ForwardEnsemble:
    """Run every draw forward, keeping exclusions as data rather than dropping them."""
    snap = snapshot or Snapshot()
    n_t = int(round(t1 - t0)) + 1
    times = np.arange(t0, t0 + n_t, 1.0)
    collected: dict[str, list[np.ndarray]] = {s: [] for s in series}
    kept: list[dict[str, Any]] = []
    exclusions: list[Exclusion] = []
    other: Counter = Counter()

    for i, p in enumerate(param_sets):
        try:
            traj = build_engine(p, snap, t0=t0).run(t0, t1)
        except ConstraintBinding as e:
            exclusions.append(Exclusion(i, e.stock, e.t, dict(p)))
            continue
        except ReservoirUndersized:
            # Never silently absorbed: a bookkeeping pool binding would
            # contaminate the exclusion counts with an arbitrary constant.
            raise
        except (ValueError, ArithmeticError, RuntimeError, KeyError) as e:
            other[type(e).__name__] += 1
            continue

        vals = {s: traj.series(s) for s in series}
        if any(not np.all(np.isfinite(v)) for v in vals.values()):
            other["NonFinite"] += 1
            continue
        for s in series:
            collected[s].append(vals[s])
        kept.append(dict(p))

    if not kept:
        raise RuntimeError(
            f"every one of {len(param_sets)} draws failed. "
            f"{len(exclusions)} were physical exclusions, others: {dict(other)}"
        )

    return ForwardEnsemble(
        times=times,
        paths={s: np.vstack(collected[s]) for s in series},
        params=kept,
        exclusions=exclusions,
        other_failures=other,
        n_requested=len(param_sets),
    )


# ------------------------------------------------------------- sensitivity


def variance_drivers(
    ens: ForwardEnsemble, series: str, year: float, top: int = 8
) -> list[tuple[str, float]]:
    """Which parameters drive spread in an outcome, by standardised regression.

    Not Sobol. Standardised regression coefficients are linear-additive and will
    understate interaction, which matters here because the technology module is
    full of them. They are used anyway because they cost one existing ensemble
    rather than a dedicated sample of tens of thousands of runs, and because the
    question being asked -- *which knobs matter at all* -- survives the
    approximation. Anything that looks decisive here deserves a proper Sobol
    index before it is believed.
    """
    y = np.log(np.clip(ens.at(series, year), 1e-300, None))
    names = free_names()
    X = np.array([[float(p[n]) for n in names] for p in ens.params])
    keep = X.std(axis=0) > 0
    X, names = X[:, keep], [n for n, k in zip(names, keep) if k]
    Xs = (X - X.mean(0)) / X.std(0)
    ys = (y - y.mean()) / (y.std() if y.std() > 0 else 1.0)
    beta, *_ = np.linalg.lstsq(
        np.hstack([Xs, np.ones((len(Xs), 1))]), ys, rcond=None
    )
    order = np.argsort(-np.abs(beta[:-1]))[:top]
    return [(names[i], float(beta[i])) for i in order]


def bifurcation_profile(
    ens: ForwardEnsemble, series: str
) -> tuple[np.ndarray, np.ndarray]:
    """When do trajectories separate fastest?

    Returns (years, growth of log-spread). The peak is the window in which the
    outcome is most sensitive to where the system already is -- the closest this
    model comes to naming a decision point, and the one §7 output that says
    something about *timing* rather than level.
    """
    p = ens.paths[series]
    spread = np.log(np.clip(np.percentile(p, 90, axis=0), 1e-300, None)) - np.log(
        np.clip(np.percentile(p, 10, axis=0), 1e-300, None)
    )
    return ens.times[1:], np.diff(spread)


def path_archetypes(
    ens: ForwardEnsemble,
    series: Sequence[str],
    k: int = 4,
    seed: int = 0,
) -> tuple[np.ndarray, dict[int, int]]:
    """Cluster trajectories into k archetypes (design §7's 'path archetypes').

    k-means on standardised log-trajectories, concatenated across series so an
    archetype is a whole-system story rather than one variable's shape. Plain
    Lloyd iteration -- the clustering is a summarisation device, not an
    inference, and using something more elaborate would suggest otherwise.
    """
    rng = np.random.default_rng(seed)
    blocks = []
    for s in series:
        v = np.log(np.clip(ens.paths[s], 1e-300, None))
        v = (v - v.mean(0)) / np.clip(v.std(0), 1e-12, None)
        blocks.append(v)
    X = np.hstack(blocks)

    centres = X[rng.choice(len(X), size=k, replace=False)]
    labels = np.zeros(len(X), dtype=int)
    for _ in range(60):
        d = ((X[:, None, :] - centres[None, :, :]) ** 2).sum(-1)
        new = d.argmin(1)
        if np.array_equal(new, labels):
            break
        labels = new
        for j in range(k):
            if (labels == j).any():
                centres[j] = X[labels == j].mean(0)
    return labels, dict(Counter(labels.tolist()))


# ---------------------------------------------------------------- manifest


def forward_manifest(
    ens: ForwardEnsemble,
    targets: Sequence[tuple[str, float, float, bool]],
    series_for_archetypes: Sequence[str],
) -> dict[str, Any]:
    labels, sizes = path_archetypes(ens, series_for_archetypes)
    out: dict[str, Any] = {
        "n_requested": ens.n_requested,
        "n_feasible": ens.n_feasible,
        "exclusion_rate": ens.exclusion_rate,
        "binding_constraints": dict(ens.binding_constraints()),
        "other_failures": dict(ens.other_failures),
        "targets": [],
        "archetype_sizes": {str(k): v for k, v in sizes.items()},
        "caveat": (
            "The model has robust backtest skill on 1 of 13 series. These are "
            "constraint and sensitivity statements, not forecasts. An exclusion "
            "means 'unreachable for the reasons this model tracks', which is "
            "weaker than 'impossible' and is the strongest claim available."
        ),
    }
    for s, yr, thr, above in targets:
        frac, text = ens.feasibility_of(s, yr, thr, above)
        out["targets"].append(
            {"series": s, "year": yr, "threshold": thr, "above": above,
             "feasible_fraction": frac, "text": text}
        )
    for s in series_for_archetypes:
        drivers = variance_drivers(ens, s, float(ens.times[-1]))
        out.setdefault("variance_drivers", {})[s] = [
            {"parameter": n, "std_beta": b} for n, b in drivers
        ]
    return out


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(manifest, indent=2) + "\n")
