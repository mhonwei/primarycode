"""Data registry: bundled snapshots first, remote fetchers when reachable.

Design §12 requires versioned data snapshots with provenance, so the *snapshot*
is the primary artefact and the network fetcher is the optional path, not the
other way round. A run is reproducible because the CSV it read is committed and
its SHA-256 is recorded in the run manifest; if the fetcher is unavailable
(sandboxed network, upstream reorganised, series revised) nothing about the run
changes.

That ordering also handles the awkward fact that upstream sources silently
revise history -- UN WPP 2022 moved world population in 1950 by ~40 million
against WPP 2019. A model whose backtest score moves when someone else
re-estimates 1950 is not measuring its own skill. Refreshing the snapshot is
therefore a deliberate, reviewable commit.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import numpy as np

from .grading import Grade, GradeProfile, SeriesMeta

BUNDLED_DIR = Path(__file__).parent / "bundled"
WORLD_CSV = BUNDLED_DIR / "world_aggregates_1950_2020.csv"


# --------------------------------------------------------------------- meta

SERIES_META: dict[str, SeriesMeta] = {
    "population_mn": SeriesMeta(
        name="population_mn",
        unit="million persons",
        grade=Grade.A,
        source="UN WPP",
        citation="UN DESA, World Population Prospects 2022, world total, mid-year.",
        note="Revised down ~40Mn at 1950 relative to WPP 2019.",
    ),
    "gdp_bn2011ppp": SeriesMeta(
        name="gdp_bn2011ppp",
        unit="billion 2011 int'l $ (PPP)",
        grade=Grade.B,
        source="Maddison Project Database 2020",
        citation=(
            "Bolt & van Zanden (2020), Maddison Project Database 2020, world "
            "aggregate. Values rounded; world totals are reconstructions, not "
            "national-accounts observations."
        ),
        note=(
            "B-grade throughout. World PPP aggregation before ~1990 rests on "
            "benchmark extrapolation; differences under ~5% are not meaningful."
        ),
    ),
    "primary_energy_ej": SeriesMeta(
        name="primary_energy_ej",
        unit="EJ / yr",
        grade=Grade.B,
        source="Energy Institute Statistical Review; Smil (2017) for pre-1965",
        citation=(
            "Energy Institute Statistical Review of World Energy (2023) for "
            "1965-2020; Smil, Energy Transitions (2017) for 1950-1964. "
            "Substitution accounting for non-fossil electricity."
        ),
        grade_by_era=((1965, Grade.A),),
        note="Pre-1965 is B-grade reconstruction; 1965+ is reported statistics.",
    ),
    "co2_emissions_gtco2": SeriesMeta(
        name="co2_emissions_gtco2",
        unit="GtCO2 / yr",
        grade=Grade.B,
        source="Global Carbon Project",
        citation=(
            "Global Carbon Budget 2023, fossil fuel combustion + cement. "
            "Excludes land-use change."
        ),
        grade_by_era=((1959, Grade.A),),
        note="Land-use-change emissions are excluded and are not negligible.",
    ),
    "co2_ppm": SeriesMeta(
        name="co2_ppm",
        unit="ppm",
        grade=Grade.B,
        source="NOAA GML (Mauna Loa); Law Dome ice core before 1959",
        citation=(
            "NOAA Global Monitoring Laboratory annual means from 1959; "
            "Law Dome DE08 firn/ice record for 1950-1958."
        ),
        grade_by_era=((1959, Grade.A),),
    ),
}


# ----------------------------------------------------------------- snapshot


@dataclass(frozen=True)
class Series:
    meta: SeriesMeta
    years: np.ndarray
    values: np.ndarray

    def window(self, y0: float, y1: float) -> "Series":
        m = (self.years >= y0) & (self.years <= y1)
        return Series(self.meta, self.years[m], self.values[m])

    def grade_profile(self) -> GradeProfile:
        p = GradeProfile()
        for y in self.years:
            p.add(self.meta.grade_at(float(y)))
        return p


class Snapshot:
    """A committed CSV of observations, addressed by content hash."""

    def __init__(self, path: Path = WORLD_CSV) -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"data snapshot missing: {self.path}")
        raw = self.path.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()

        rows: dict[str, list[tuple[float, float]]] = {}
        lines = raw.decode("utf-8").strip().splitlines()
        header = [h.strip() for h in lines[0].split(",")]
        if header != ["year", "series", "value"]:
            raise ValueError(f"unexpected snapshot header: {header}")
        for ln in lines[1:]:
            if not ln.strip():
                continue
            y, s, v = ln.split(",")
            rows.setdefault(s.strip(), []).append((float(y), float(v)))

        self._series: dict[str, Series] = {}
        for name, pts in rows.items():
            pts.sort()
            meta = SERIES_META.get(name)
            if meta is None:
                raise KeyError(
                    f"series {name!r} is in the snapshot but has no registered "
                    "metadata. Every series must carry source and grade."
                )
            ys = np.array([p[0] for p in pts])
            vs = np.array([p[1] for p in pts])
            if not np.all(np.isfinite(vs)):
                raise ValueError(f"series {name!r} contains non-finite values")
            self._series[name] = Series(meta, ys, vs)

    def __contains__(self, name: str) -> bool:
        return name in self._series

    def series(self, name: str) -> Series:
        try:
            return self._series[name]
        except KeyError:
            raise KeyError(
                f"no series {name!r} in snapshot {self.path.name}; "
                f"available: {sorted(self._series)}"
            ) from None

    @property
    def names(self) -> list[str]:
        return sorted(self._series)

    def grade_profile(self, names: Iterable[str] | None = None) -> GradeProfile:
        p = GradeProfile()
        for n in names if names is not None else self.names:
            for y in self.series(n).years:
                p.add(self.series(n).meta.grade_at(float(y)))
        return p

    def manifest(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "sha256": self.sha256,
            "series": {
                n: {
                    "unit": s.meta.unit,
                    "source": s.meta.source,
                    "grade": s.meta.grade.value,
                    "n": int(len(s.years)),
                    "span": [float(s.years[0]), float(s.years[-1])],
                }
                for n, s in self._series.items()
            },
        }


# ------------------------------------------------------------------ fetchers

#: Remote refreshers, wired but optional. Each returns rows of (year, value).
#: They are exercised only by `civsim.data.refresh`, never during a run.
REMOTE_FETCHERS: dict[str, Callable[[], list[tuple[float, float]]]] = {}


def register_fetcher(
    series: str,
) -> Callable[[Callable[[], list[tuple[float, float]]]], Callable]:
    def deco(fn):
        REMOTE_FETCHERS[series] = fn
        return fn

    return deco


def interpolate(series: Series, years: Iterable[float]) -> np.ndarray:
    """Linear interpolation onto `years`, NaN outside the observed span.

    Interpolated points are *not* observations. Callers that score against them
    must downgrade the result to C-grade; `backtest` refuses to score off-grid
    years for exactly this reason.
    """
    ys = np.asarray(list(years), dtype=float)
    out = np.interp(ys, series.years, series.values, left=math.nan, right=math.nan)
    return out
