"""Command line entry point.

    python -m civsim selftest    conservation and protocol checks, no fitting
    python -m civsim prior       print the prior
    python -m civsim backtest    the M3 run: fit 1950-1990, score 1990-2020
    python -m civsim stability   re-run across seeds; only robust verdicts
    python -m civsim rolling     rolling-origin evaluation across four cutoffs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from .backtest.runner import prior_report, run_backtest
from .data.registry import Snapshot
from .model import build_engine
from .uncertainty.priors import sample_prior

OUT = Path("out")


def cmd_prior(args: argparse.Namespace) -> int:
    print(prior_report())
    return 0


def cmd_selftest(args: argparse.Namespace) -> int:
    snap = Snapshot()
    print(f"snapshot {snap.path.name} sha256={snap.sha256}")
    print(f"series:  {', '.join(snap.names)}")
    print(f"grades:  {snap.grade_profile().describe()}")
    print(f"caveat:  {snap.grade_profile().caveat()}")

    rng = np.random.default_rng(0)
    params = sample_prior(rng, 24)
    print(f"\nintegrating {len(params)} prior draws 1950-2020 with checks on...")
    ok = 0
    for p in params:
        eng = build_engine(p, snap, t0=1950.0, check_conservation=True)
        try:
            eng.run(1950.0, 2020.0)
        except Exception as e:  # noqa: BLE001 - reported, not swallowed
            print(f"  draw failed: {type(e).__name__}: {str(e)[:110]}")
            continue
        ok += 1
        for b in eng.ledger.balances():
            assert b.ok, b
        eng.financial.check(2020.0)
    print(f"  {ok}/{len(params)} integrated with all conservation checks green")
    return 0 if ok else 1


def cmd_backtest(args: argparse.Namespace) -> int:
    from .viz.fan import fan_figure

    report = run_backtest(
        n_draws=args.draws,
        n_resample=args.resample,
        seed=args.seed,
        verbose=True,
    )

    print("\n" + report.summary_table())
    print("\nverdicts (§11.2 -- reported whether flattering or not):")
    print(report.verdicts())

    OUT.mkdir(exist_ok=True)
    fig = fan_figure(report, OUT / "m3_backtest_fan.png")
    report.write_manifest(OUT / "m3_backtest_manifest.json")
    report.holdout.write_manifest(OUT / "m3_protocol.json")
    print(f"\nwrote {fig}")
    print(f"wrote {OUT / 'm3_backtest_manifest.json'}")
    print(f"wrote {OUT / 'm3_protocol.json'}")

    n = len(report.scores)
    print(
        f"\nM3 exit criterion: model beat every baseline on "
        f"{report.n_beaten}/{n} series."
    )
    return 0


def cmd_stability(args: argparse.Namespace) -> int:
    """Re-run the backtest across seeds and report which verdicts survive.

    A skill score computed on six scored points carries Monte Carlo error large
    enough to flip its sign between runs -- observed directly here, where GDP
    moved from +5.7% to -14.7% on nothing but a change in particle count. A
    single-seed skill number is therefore not a result, and quoting one would be
    the quantitative equivalent of reporting a coin flip. Only verdicts that
    hold sign across seeds are reported as findings.
    """
    from .model import OBSERVED_SERIES

    skills: dict[str, list[float]] = {s: [] for s in OBSERVED_SERIES}
    for seed in range(args.seed, args.seed + args.repeats):
        rep = run_backtest(
            n_draws=args.draws, n_resample=args.resample, seed=seed, verbose=False
        )
        for name, sc in rep.scores.items():
            skills[name].append(sc.skill_vs_best)
        print(f"  seed {seed}: beat baselines on {rep.n_beaten}/{len(rep.scores)}")

    print(
        f"\n{'series':<22} {'mean':>9} {'min':>9} {'max':>9}   verdict "
        f"across {args.repeats} seeds"
    )
    print("-" * 84)
    robust = 0
    for name, vals in skills.items():
        v = np.array(vals)
        if (v > 0).all():
            verdict, robust = "ROBUST SKILL", robust + 1
        elif (v < 0).all():
            verdict = "ROBUST LOSS"
        else:
            verdict = "SIGN UNSTABLE -> indistinguishable from baseline"
        print(
            f"{name:<22} {100 * v.mean():>+8.1f}% {100 * v.min():>+8.1f}% "
            f"{100 * v.max():>+8.1f}%   {verdict}"
        )
    print(
        f"\nRobust skill on {robust}/{len(skills)} series. Anything marked "
        "SIGN UNSTABLE must be reported as no demonstrated skill."
    )
    return 0


def cmd_rolling(args: argparse.Namespace) -> int:
    from .backtest.rolling import DEFAULT_ORIGINS, run_rolling

    from .backtest.rolling import CONTROL_ORIGINS

    if args.control:
        res = run_rolling(
            origins=CONTROL_ORIGINS,
            fixed_test_start=args.fixed_test,
            n_draws=args.draws,
            n_resample=args.resample,
            seed=args.seed,
            verbose=True,
        )
    else:
        res = run_rolling(
            origins=DEFAULT_ORIGINS,
            n_draws=args.draws,
            n_resample=args.resample,
            seed=args.seed,
            verbose=True,
        )
    print("\n" + res.table())
    print("\n" + res.discrepancy_table())
    print("\n" + res.non_stationarity_summary())

    OUT.mkdir(exist_ok=True)
    res.write_manifest(OUT / "m3_rolling_manifest.json")
    print(f"\nwrote {OUT / 'm3_rolling_manifest.json'}")

    robust = sum(1 for n in res.series if res.verdict(n) == "ROBUST SKILL")
    print(
        f"\nRobust skill across all {len(res.origins)} origins on "
        f"{robust}/{len(res.series)} series."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="civsim")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("prior").set_defaults(fn=cmd_prior)
    sub.add_parser("selftest").set_defaults(fn=cmd_selftest)

    bt = sub.add_parser("backtest")
    bt.add_argument("--draws", type=int, default=1500,
                    help="SMC particles")
    bt.add_argument("--resample", type=int, default=2000,
                    help="baseline ensemble size")
    bt.add_argument("--seed", type=int, default=20260726)
    bt.set_defaults(fn=cmd_backtest)

    st = sub.add_parser("stability")
    st.add_argument("--draws", type=int, default=1000)
    st.add_argument("--resample", type=int, default=1500)
    st.add_argument("--seed", type=int, default=1)
    st.add_argument("--repeats", type=int, default=5)
    st.set_defaults(fn=cmd_stability)

    ro = sub.add_parser("rolling")
    ro.add_argument("--draws", type=int, default=900)
    ro.add_argument("--resample", type=int, default=1200)
    ro.add_argument("--seed", type=int, default=20260726)
    ro.add_argument("--control", action="store_true",
                    help="fixed test window; isolates non-stationarity from "
                         "test-window length")
    ro.add_argument("--fixed-test", type=float, default=1995.0)
    ro.set_defaults(fn=cmd_rolling)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
