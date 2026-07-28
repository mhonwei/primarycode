"""Command line entry point.

    python -m civsim selftest    conservation and protocol checks, no fitting
    python -m civsim prior       print the prior
    python -m civsim backtest    the M3 run: fit 1950-1990, score 1990-2020
    python -m civsim stability   re-run across seeds; only robust verdicts
    python -m civsim rolling     rolling-origin evaluation across four cutoffs
    python -m civsim forward     project to 2100; what is ruled out, and by what
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


def cmd_forward(args: argparse.Namespace) -> int:
    """Calibrate on all history, project forward, report what is ruled out.

    There is no hold-out here and no skill claim. The hold-out gate exists to
    keep test data out of a *fit*; this run scores nothing, so it calibrates on
    everything 1950-2020 and projects. What it reports -- exclusions, variance
    drivers, path archetypes -- are statements about constraint structure, and
    those are the §7 outputs that do not need the model to forecast well. Which
    is fortunate, because it forecasts well on 1 of 13 series.
    """
    import numpy as _np

    from .backtest.protocol import Observation
    from .data.registry import Snapshot as _Snap
    from .forward import (
        forward_manifest,
        path_archetypes,
        project,
        variance_drivers,
        write_manifest,
    )
    from .model import OBSERVED_SERIES
    from .uncertainty.sampler import Posterior, loglik_paths
    from .uncertainty.smc import run_smc

    snap = _Snap()
    full = {}
    for name in OBSERVED_SERIES:
        w = snap.series(name).window(1950.0, 2020.0)
        full[name] = Observation(name, w.years, w.values, w.grade_profile())

    print(f"calibrate  1950-2020, all {len(OBSERVED_SERIES)} series, no hold-out")
    print("           (no skill is claimed by this command; see README)")

    def loglik_fn(paths, times, ok):
        return loglik_paths(paths, times, full, snap)

    smc = run_smc(
        loglik_fn, snap, t0=1950.0, t1=2020.0,
        n_particles=args.draws, seed=args.seed, series=OBSERVED_SERIES,
        verbose=True,
    )
    post = Posterior.from_smc(smc)
    print(f"posterior  {post.health()}")

    print(f"project    {post.n_particles} posterior draws to {args.to:.0f}")
    ens = project(post.params, snap, t0=1950.0, t1=float(args.to))
    print("\n" + ens.exclusion_report())

    targets = [
        ("co2_ppm", float(args.to), 450.0, False),
        ("co2_ppm", float(args.to), 550.0, False),
        ("primary_energy_ej", float(args.to), 1000.0, True),
        ("lowcarbon_share_pct", float(args.to), 50.0, True),
        ("population_mn", float(args.to), 10000.0, False),
    ]
    print("\nreachability of stated targets (denominator includes exclusions):")
    for t in targets:
        print("  " + ens.feasibility_of(t[0], t[1], t[2], t[3])[1])

    key = ["population_mn", "gdp_bn2011ppp", "primary_energy_ej", "co2_ppm"]
    print("\nvariance drivers at %d (standardised regression, not Sobol):" % args.to)
    for s in key:
        drv = variance_drivers(ens, s, float(args.to), top=4)
        print("  %-22s %s" % (s, ", ".join(f"{n} {b:+.2f}" for n, b in drv)))

    _, sizes = path_archetypes(ens, key, k=4, seed=args.seed)
    print("\npath archetypes (k=4): sizes %s" % sorted(sizes.values(), reverse=True))

    from .viz.forward import forward_figure

    OUT.mkdir(exist_ok=True)
    write_manifest(
        OUT / "m4_forward_manifest.json", forward_manifest(ens, targets, key)
    )
    verdicts = {
        "population_mn": "ROBUST SKILL +34%",
        "gdp_bn2011ppp": "ROBUST LOSS -141%",
        "primary_energy_ej": "ROBUST LOSS -247%",
        "co2_ppm": "ROBUST LOSS -256%",
        "lowcarbon_share_pct": "ROBUST LOSS -336%",
        "co2_emissions_gtco2": "ROBUST LOSS -370%",
    }
    panels = ["population_mn", "gdp_bn2011ppp", "primary_energy_ej",
              "lowcarbon_share_pct", "co2_emissions_gtco2", "co2_ppm"]
    fig = forward_figure(ens, panels, OUT / "m4_forward.png", verdicts)
    print(f"\nwrote {OUT / 'm4_forward_manifest.json'}")
    print(f"wrote {fig}")
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

    fw = sub.add_parser("forward")
    fw.add_argument("--draws", type=int, default=800)
    fw.add_argument("--to", type=float, default=2100.0)
    fw.add_argument("--seed", type=int, default=20260726)
    fw.set_defaults(fn=cmd_forward)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
