"""Rolling-origin evaluation.

A single 1990 cutoff gives six scored points. That is not enough to resolve a
skill difference: M1's GDP skill moved from +5.7% to -14.7% on nothing but a
change in particle count, and across seeds its sign was unstable on three of
five series. Reporting one number from one cutoff is reporting noise with a
decimal point on it.

Rolling origins fix two things at once.

**Sample size.** Each origin contributes its own scored points, so the evidence
base grows from six to several dozen without inventing data.

**Non-stationarity, tested rather than asserted.** Design §2.2 claims that
parameters fitted on one regime fail on the next, and M0/M1 both showed it
qualitatively. With origins at 1975, 1985, 1995 and 2005 the claim becomes
measurable: if it is true, skill should *degrade systematically as the origin
moves later*, because each later calibration window ends closer to a structural
break it cannot see. If skill is flat across origins, the non-stationarity story
is weaker than the design assumes and should be weakened in the design.

What rolling origins do **not** fix: the test windows overlap (all end in 2020),
so scores across origins are correlated and cannot be treated as independent
replicates. The spread across origins is a diagnostic, not a confidence
interval. And hindsight leakage (§2.6) is untouched -- the author knows what
happened after every one of these cutoffs.

Each origin runs the full protocol independently: its own prior, its own SMC,
its own freeze, its own reveal. Nothing is shared between origins except the
model code and the snapshot, so an origin cannot borrow information from a
later origin's test window.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from ..data.registry import Snapshot
from ..model import OBSERVED_SERIES
from .runner import BacktestReport, run_backtest

#: Origins for the 5-yearly world snapshot. 1975 is the earliest that leaves a
#: calibration window able to identify anything (six points); 2005 is the latest
#: that leaves a test window worth scoring (three points).
DEFAULT_ORIGINS = (1975.0, 1985.0, 1995.0, 2005.0)


@dataclass
class RollingResult:
    origins: list[float]
    reports: list[BacktestReport]
    series: tuple[str, ...]
    seed: int
    inferred_discrepancy: dict[float, dict[str, float]] = field(default_factory=dict)

    # ---------------------------------------------------------------- views

    def skill(self, name: str) -> np.ndarray:
        return np.array([r.scores[name].skill_vs_best for r in self.reports])

    def n_points(self, name: str) -> int:
        return sum(len(r.scores[name].years) for r in self.reports)

    def pooled_skill(self, name: str) -> float:
        """Skill on CRPS pooled over every scored point at every origin.

        Pooling the scores rather than averaging the per-origin skill ratios
        keeps origins with more scored points weighted more heavily, which is
        what they deserve -- a 1975 origin scores nine points, a 2005 origin
        three.
        """
        m = np.concatenate([r.scores[name].model_crps for r in self.reports])
        b = np.concatenate(
            [
                r.scores[name].baseline_crps[r.scores[name].best_baseline[0]]
                for r in self.reports
            ]
        )
        bm, bb = float(np.mean(m)), float(np.mean(b))
        return 1.0 - bm / bb if bb > 0 else float("nan")

    def verdict(self, name: str) -> str:
        s = self.skill(name)
        if (s > 0).all():
            return "ROBUST SKILL"
        if (s < 0).all():
            return "ROBUST LOSS"
        return "SIGN UNSTABLE"

    def origin_trend(self, name: str) -> float:
        """OLS slope of skill against origin year, in skill points per decade.

        Negative means later origins do worse -- the signature §2.2 predicts.
        """
        x = np.array(self.origins)
        y = self.skill(name)
        if len(x) < 2 or np.allclose(x, x[0]):
            return float("nan")
        return float(np.polyfit(x, y, 1)[0] * 10.0)

    # --------------------------------------------------------------- report

    def table(self) -> str:
        w = 26
        head = (
            f"{'series':<{w}} {'pooled':>8} {'pts':>4}  "
            + "".join(f"{int(o):>8}" for o in self.origins)
            + f"  {'trend/dec':>10}  verdict"
        )
        lines = [head, "-" * (len(head) + 2)]
        for name in self.series:
            s = self.skill(name)
            lines.append(
                f"{name:<{w}} {100 * self.pooled_skill(name):>+7.1f}% "
                f"{self.n_points(name):>4}  "
                + "".join(f"{100 * v:>+7.0f}%" for v in s)
                + f"  {100 * self.origin_trend(name):>+9.1f}  {self.verdict(name)}"
            )
        return "\n".join(lines)

    def discrepancy_table(self) -> str:
        """Inferred structural error per series, per origin."""
        if not self.inferred_discrepancy:
            return ""
        w = 26
        head = (
            f"{'series':<{w}}"
            + "".join(f"{int(o):>9}" for o in self.origins)
            + "   (inferred structural error, log scale)"
        )
        lines = [head, "-" * (len(head) - 38)]
        for name in self.series:
            vals = [
                self.inferred_discrepancy.get(o, {}).get(name, float("nan"))
                for o in self.origins
            ]
            lines.append(
                f"{name:<{w}}" + "".join(f"{100 * v:>8.1f}%" for v in vals)
            )
        return "\n".join(lines)

    def non_stationarity_summary(self) -> str:
        trends = {n: self.origin_trend(n) for n in self.series}
        finite = {k: v for k, v in trends.items() if np.isfinite(v)}
        if not finite:
            return "no origin trend computable"
        worse = sum(1 for v in finite.values() if v < 0)
        mean = float(np.mean(list(finite.values())))
        line = (
            f"Skill vs origin year: {worse}/{len(finite)} series degrade as the "
            f"origin moves later; mean trend {100 * mean:+.1f} skill points per "
            "decade."
        )
        if worse > len(finite) / 2 and mean < 0:
            return line + (
                "\n  Consistent with design §2.2: calibration windows ending "
                "closer to a structural break generalise worse."
            )
        return line + (
            "\n  NOT the pattern §2.2 predicts. Either the breaks are not where "
            "the design assumes, or origin-to-origin noise swamps the effect at "
            "this sample size. Do not quote §2.2 as demonstrated here."
        )

    def manifest(self) -> dict[str, Any]:
        return {
            "origins": self.origins,
            "seed": self.seed,
            "series": list(self.series),
            "pooled_skill": {n: self.pooled_skill(n) for n in self.series},
            "per_origin_skill": {
                n: [float(v) for v in self.skill(n)] for n in self.series
            },
            "scored_points": {n: self.n_points(n) for n in self.series},
            "origin_trend_per_decade": {
                n: self.origin_trend(n) for n in self.series
            },
            "verdict": {n: self.verdict(n) for n in self.series},
            "inferred_discrepancy": {
                str(o): d for o, d in self.inferred_discrepancy.items()
            },
            "protocols": [r.holdout.manifest() for r in self.reports],
        }

    def write_manifest(self, path: Path) -> None:
        Path(path).write_text(json.dumps(self.manifest(), indent=2) + "\n")


#: Origins for the fixed-test-window control (see `fixed_test_start`).
CONTROL_ORIGINS = (1975.0, 1985.0, 1995.0)


def run_rolling(
    origins: Sequence[float] = DEFAULT_ORIGINS,
    snapshot: Snapshot | None = None,
    end: float = 2020.0,
    start: float = 1950.0,
    series: Sequence[str] = OBSERVED_SERIES,
    n_draws: int = 900,
    n_resample: int = 1200,
    seed: int = 20260726,
    fixed_test_start: float | None = None,
    verbose: bool = True,
) -> RollingResult:
    """Run the full protocol independently at each origin.

    With `fixed_test_start` set, every origin is scored on the *same* window and
    only the calibration end moves. That control matters: in the default
    expanding-window design, later origins get both more calibration data and a
    shorter test window, so a downward skill trend could be non-stationarity or
    could just be three scored points being noisy. Holding the test window fixed
    removes the second explanation and leaves an asymmetric test -- later origins
    have strictly *more* data, so if skill still degrades, that is hard to
    explain by anything but the calibration window ending closer to a break.
    """
    from ..uncertainty.sampler import inferred_discrepancy

    snap = snapshot or Snapshot()
    reports: list[BacktestReport] = []
    discrep: dict[float, dict[str, float]] = {}

    for origin in origins:
        test_start = fixed_test_start if fixed_test_start is not None else origin
        if test_start < origin:
            raise ValueError(
                f"fixed test window starts {test_start:g}, before origin "
                f"{origin:g}; that would calibrate on scored years"
            )
        if verbose:
            print(
                f"\n=== origin {int(origin)}: calibrate {int(start)}-{int(origin)}, "
                f"score {int(test_start)}-{int(end)} ==="
            )
        rep = run_backtest(
            snapshot=snap,
            calib=(start, origin),
            test=(test_start, end),
            series=series,
            n_draws=n_draws,
            n_resample=n_resample,
            # Vary the seed by origin so a single unlucky draw cannot make the
            # origin trend look like a finding.
            seed=seed + int(origin),
            verbose=False,
        )
        reports.append(rep)
        discrep[origin] = inferred_discrepancy(
            {s: rep.posterior.paths(s) for s in series},
            rep.posterior.times,
            rep.holdout.calibration(),
            snap,
        )
        if verbose:
            print(
                f"  beat baselines on {rep.n_beaten}/{len(series)}; "
                f"{rep.posterior.n_unique} unique particles"
            )

    return RollingResult(
        origins=[float(o) for o in origins],
        reports=reports,
        series=tuple(series),
        seed=seed,
        inferred_discrepancy=discrep,
    )
