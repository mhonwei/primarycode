"""A/B/C data grading (design §10.1).

    A -- direct observation
    B -- statistical estimate
    C -- model inference

The rule the design commits to is that *any model output must be able to report
how much C-grade data it rests on*. That is only enforceable if grade travels
with the series rather than living in a footnote, so grade is part of
:class:`SeriesMeta` and every consumer that combines series produces a
:class:`GradeProfile`.

This is not bookkeeping for its own sake. Pre-1800 GDP figures are C-grade --
they are Maddison's model output, not measurements -- and calibrating on them
and then quoting precision is the circularity §4 of the design warns about. The
grade profile is what makes that visible at the point of use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Grade(str, Enum):
    A = "A"  # direct observation
    B = "B"  # statistical estimate
    C = "C"  # model inference

    @property
    def rank(self) -> int:
        return {"A": 0, "B": 1, "C": 2}[self.value]


@dataclass(frozen=True)
class SeriesMeta:
    name: str
    unit: str
    grade: Grade
    source: str
    #: Where the numbers came from, precise enough to re-derive them.
    citation: str
    note: str = ""
    #: Grade can differ by era; entries are (from_year, grade), sorted.
    grade_by_era: tuple[tuple[int, Grade], ...] = ()

    def grade_at(self, year: float) -> Grade:
        best = self.grade
        for start, g in self.grade_by_era:
            if year >= start:
                best = g
        return best


@dataclass
class GradeProfile:
    """Grade composition of the data underlying a result."""

    counts: dict[Grade, int] = field(default_factory=dict)

    def add(self, grade: Grade, n: int = 1) -> None:
        self.counts[grade] = self.counts.get(grade, 0) + n

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    def share(self, grade: Grade) -> float:
        return self.counts.get(grade, 0) / self.total if self.total else 0.0

    @property
    def worst(self) -> Grade:
        present = [g for g, n in self.counts.items() if n]
        return max(present, key=lambda g: g.rank) if present else Grade.A

    def describe(self) -> str:
        if not self.total:
            return "no data points"
        parts = [
            f"{g.value}:{self.counts.get(g, 0)} ({self.share(g):.0%})"
            for g in (Grade.A, Grade.B, Grade.C)
            if self.counts.get(g)
        ]
        return f"{self.total} points -- " + ", ".join(parts)

    def caveat(self) -> str:
        """One line to attach to any reported result."""
        c = self.share(Grade.C)
        b = self.share(Grade.B)
        if c >= 0.25:
            return (
                f"{c:.0%} of underlying points are C-grade (model inference). "
                "Do not quote precision from this result."
            )
        if b + c >= 0.5:
            return (
                f"{b + c:.0%} of underlying points are estimates rather than "
                "observations; treat differences smaller than the estimate "
                "spread as noise."
            )
        return "predominantly observational (A-grade) inputs."
