"""Hold-out protocol -- §11.1 and §11.7 made unbypassable.

The design commits to two things that are easy to write down and easy to violate
by accident:

  §11.1  calibrate on one window, score on a later, disjoint one. Never
         calibrate on 1950-2020 and then "backtest" 1950-2020.
  §11.7  freeze the model structure and priors *before* looking at the test
         window, and record every change made afterwards.

Discipline alone does not survive contact with a debugging session at 2am. So
the test data is not merely something one is asked not to fit -- it is behind a
gate. :meth:`Holdout.calibration` hands out the pre-cutoff observations freely.
:meth:`Holdout.reveal_test` refuses to return anything until :meth:`freeze` has
been called, and records that the reveal happened. Any later attempt to re-fit
raises.

This does not prevent the deeper problem. The designer of this model already
knows what 1990-2020 looked like, and that knowledge leaks through every choice
of functional form (§2.6). No amount of gating fixes hindsight leakage; what the
gate does is make the *mechanical* version of the error impossible and force the
judgement version to be logged, in the changelog, where a reader can weigh it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from ..data.grading import Grade, GradeProfile
from ..data.registry import Series, Snapshot


class ProtocolViolation(RuntimeError):
    """An operation would have leaked test-window information into fitting."""


@dataclass
class Observation:
    series: str
    years: np.ndarray
    values: np.ndarray
    grade_profile: GradeProfile


@dataclass
class Holdout:
    """A calibration/test split over a snapshot."""

    snapshot: Snapshot
    calib: tuple[float, float]
    test: tuple[float, float]
    series: tuple[str, ...]
    _frozen: bool = field(default=False, init=False)
    _revealed: bool = field(default=False, init=False)
    _freeze_record: dict = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.calib[1] > self.test[0]:
            raise ProtocolViolation(
                f"calibration window {self.calib} overlaps test window "
                f"{self.test}. §11.1 requires disjoint windows: fitting and "
                "scoring on the same years measures fit, not skill."
            )
        for s in self.series:
            if s not in self.snapshot:
                raise KeyError(f"series {s!r} not in snapshot")

    # ------------------------------------------------------------- windows

    def _obs(self, s: str, lo: float, hi: float) -> Observation:
        w: Series = self.snapshot.series(s).window(lo, hi)
        return Observation(s, w.years, w.values, w.grade_profile())

    def calibration(self) -> dict[str, Observation]:
        """Pre-cutoff observations. Always available."""
        return {s: self._obs(s, *self.calib) for s in self.series}

    @property
    def frozen(self) -> bool:
        return self._frozen

    @property
    def revealed(self) -> bool:
        return self._revealed

    def freeze(self, note: str, extra: dict | None = None) -> None:
        """Lock the fit. Must be called before the test window is readable."""
        if self._frozen:
            raise ProtocolViolation(
                "already frozen; re-freezing after seeing test data is exactly "
                "the move §11.7 exists to prevent. Start a new run instead."
            )
        self._frozen = True
        self._freeze_record = {
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "note": note,
            "calibration_window": list(self.calib),
            "test_window": list(self.test),
            "series": list(self.series),
            "snapshot_sha256": self.snapshot.sha256,
            **(extra or {}),
        }

    def reveal_test(self) -> dict[str, Observation]:
        if not self._frozen:
            raise ProtocolViolation(
                "test window requested before freeze(). Fit on "
                f"{self.calib}, call freeze(), then score on {self.test}."
            )
        self._revealed = True
        return {s: self._obs(s, *self.test) for s in self.series}

    def assert_fit_allowed(self) -> None:
        """Called by anything that adjusts parameters."""
        if self._revealed:
            raise ProtocolViolation(
                "parameters cannot be adjusted after the test window has been "
                "revealed. Whatever this change is, it is being made with "
                "knowledge of the answer."
            )

    # ------------------------------------------------------------ reporting

    def scoring_years(self) -> np.ndarray:
        """Years scored: observed grid points inside the test window only.

        Interpolated years are refused. Scoring against interpolation measures
        agreement with `numpy.interp`, not with the world, and would silently
        inflate the sample size that skill statistics are computed over.
        """
        any_series = self.snapshot.series(self.series[0])
        m = (any_series.years > self.test[0]) & (any_series.years <= self.test[1])
        return any_series.years[m]

    def manifest(self) -> dict:
        prof = GradeProfile()
        for s in self.series:
            for y in self.snapshot.series(s).years:
                prof.add(self.snapshot.series(s).meta.grade_at(float(y)))
        return {
            **self._freeze_record,
            "frozen": self._frozen,
            "test_revealed": self._revealed,
            "grade_profile": {g.value: prof.counts.get(g, 0) for g in Grade},
            "grade_caveat": prof.caveat(),
        }

    def write_manifest(self, path: Path) -> None:
        Path(path).write_text(json.dumps(self.manifest(), indent=2) + "\n")
