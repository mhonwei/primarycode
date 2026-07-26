"""Hold-out gating (§11.1, §11.7) and scoring properties (§11.2)."""

from __future__ import annotations

import numpy as np
import pytest

from civsim.backtest.baselines import DEFAULT_BASELINES
from civsim.backtest.protocol import Holdout, ProtocolViolation
from civsim.backtest.scoring import crps_ensemble, mae, skill_score
from civsim.data.grading import Grade, GradeProfile
from civsim.data.registry import Snapshot
from civsim.model import OBSERVED_SERIES
from civsim.uncertainty.sampler import effective_n_obs


@pytest.fixture(scope="module")
def snap():
    return Snapshot()


@pytest.fixture
def holdout(snap):
    return Holdout(snap, (1950.0, 1990.0), (1990.0, 2020.0), tuple(OBSERVED_SERIES))


# ------------------------------------------------------------- the gate


def test_overlapping_windows_rejected(snap):
    with pytest.raises(ProtocolViolation, match="overlaps test window"):
        Holdout(snap, (1950.0, 2000.0), (1990.0, 2020.0), ("population_mn",))


def test_test_window_unreadable_before_freeze(holdout):
    with pytest.raises(ProtocolViolation, match="before freeze"):
        holdout.reveal_test()


def test_calibration_always_readable(holdout):
    obs = holdout.calibration()
    assert set(obs) == set(OBSERVED_SERIES)
    for o in obs.values():
        assert o.years.max() <= 1990.0, "calibration leaked a post-cutoff year"


def test_fitting_after_reveal_is_refused(holdout):
    holdout.freeze(note="test")
    holdout.reveal_test()
    with pytest.raises(ProtocolViolation, match="knowledge of the answer"):
        holdout.assert_fit_allowed()


def test_refreezing_is_refused(holdout):
    holdout.freeze(note="first")
    with pytest.raises(ProtocolViolation, match="already frozen"):
        holdout.freeze(note="second")


def test_scoring_years_exclude_calibration(holdout):
    ys = holdout.scoring_years()
    assert ys.min() > 1990.0
    assert ys.max() <= 2020.0
    assert list(ys) == [1995, 2000, 2005, 2010, 2015, 2020]


def test_manifest_records_the_gate(holdout):
    holdout.freeze(note="n")
    holdout.reveal_test()
    m = holdout.manifest()
    assert m["frozen"] and m["test_revealed"]
    assert m["snapshot_sha256"]
    assert "grade_profile" in m


# ------------------------------------------------------------ likelihood


def test_correlated_years_count_for_less_than_their_number():
    years = np.arange(1950.0, 1995.0, 5.0)
    n_eff = effective_n_obs(years, corr_years=25.0)
    assert 1.0 < n_eff < len(years) / 2, (
        "a smooth 40-year series must not count as 9 independent observations; "
        "that is what collapses the sampler"
    )


def test_zero_correlation_recovers_independent_count():
    years = np.arange(1950.0, 1995.0, 5.0)
    assert effective_n_obs(years, corr_years=1e-9) == pytest.approx(len(years))


# -------------------------------------------------------------- scoring


def test_crps_of_a_degenerate_ensemble_is_absolute_error():
    ens = np.full(500, 3.0)
    assert crps_ensemble(ens, 5.0) == pytest.approx(2.0, abs=1e-9)


def test_crps_rewards_being_right():
    rng = np.random.default_rng(0)
    good = rng.normal(5.0, 1.0, 4000)
    bad = rng.normal(9.0, 1.0, 4000)
    assert crps_ensemble(good, 5.0) < crps_ensemble(bad, 5.0)


def test_crps_penalises_both_overconfidence_and_vagueness():
    rng = np.random.default_rng(1)
    truth = 5.0
    calibrated = rng.normal(5.0, 1.0, 8000)
    overconfident = rng.normal(7.0, 0.05, 8000)
    vague = rng.normal(5.0, 20.0, 8000)
    c = crps_ensemble(calibrated, truth)
    assert c < crps_ensemble(overconfident, truth)
    assert c < crps_ensemble(vague, truth)


def test_skill_score_sign_and_undefined_case():
    assert skill_score(1.0, 2.0) == pytest.approx(0.5)
    assert skill_score(2.0, 1.0) == pytest.approx(-1.0)
    assert np.isnan(skill_score(1.0, 0.0))


def test_mae_matches_numpy():
    a = np.array([1.0, 2.0, 3.0])
    b = np.array([1.5, 1.0, 4.0])
    assert mae(a, b) == pytest.approx(np.mean(np.abs(a - b)))


# ------------------------------------------------------------- baselines


@pytest.mark.parametrize("baseline", DEFAULT_BASELINES, ids=lambda b: b.name)
def test_baselines_emit_positive_spread_ensembles(baseline, snap):
    s = snap.series("gdp_bn2011ppp")
    m = s.years <= 1990
    fc = baseline.forecast(
        s.years[m], s.values[m], np.array([1995.0, 2005.0, 2020.0]),
        np.random.default_rng(0), n=400,
    )
    assert fc.ensemble.shape == (400, 3)
    assert np.all(fc.ensemble > 0), "log-space baselines must stay positive"
    spread = fc.ensemble.std(axis=0)
    assert np.all(spread > 0), "a point forecast cannot be scored against a fan"
    assert spread[-1] >= spread[0], "uncertainty must not shrink with horizon"


# ----------------------------------------------------------------- data


def test_every_series_carries_source_and_grade(snap):
    for n in snap.names:
        meta = snap.series(n).meta
        assert meta.source and meta.citation
        assert isinstance(meta.grade, Grade)


def test_grade_varies_by_era(snap):
    ppm = snap.series("co2_ppm").meta
    assert ppm.grade_at(1955) is Grade.B  # ice core
    assert ppm.grade_at(1990) is Grade.A  # Mauna Loa


def test_grade_profile_caveat_escalates():
    p = GradeProfile()
    p.add(Grade.C, 8)
    p.add(Grade.A, 2)
    assert "C-grade" in p.caveat()
    assert p.worst is Grade.C


def test_snapshot_hash_is_stable(snap):
    assert snap.sha256 == Snapshot().sha256
    assert len(snap.sha256) == 64


# ------------------------------------------- per-series discrepancy (M2)


def test_marginal_t_charges_a_bad_channel_logarithmically():
    """The point of integrating out the scale.

    Under a fixed-scale Gaussian, doubling a residual quadruples its penalty, so
    one badly modelled channel dominates the joint likelihood and drags shared
    parameters. Under the marginal-t the penalty is logarithmic in the quadratic
    form, so the channel reports itself as poorly modelled instead.
    """
    from civsim.uncertainty.sampler import (
        DISCREPANCY_IG_A,
        DISCREPANCY_IG_B,
        STRUCTURAL_SCALE,
        SeriesLik,
    )

    q_small, q_large = 1.0, 100.0
    small = SeriesLik("s", np.array([q_small]), n=9, logdet=0.0)
    large = SeriesLik("s", np.array([q_large]), n=9, logdet=0.0)

    t_gap = float(
        small.loglik(DISCREPANCY_IG_A, DISCREPANCY_IG_B)[0]
        - large.loglik(DISCREPANCY_IG_A, DISCREPANCY_IG_B)[0]
    )
    # The shape matrix carries no scale, so M1's fixed-scale Gaussian charged
    # Q / (2 sigma^2) -- with sigma = 6% that is a factor of ~139 on top of Q.
    # Forgetting that factor is what makes the uniform-scale likelihood look
    # harmless on paper and lets one channel dominate in practice.
    gauss_gap = 0.5 * (q_large - q_small) / STRUCTURAL_SCALE**2
    assert 0 < t_gap < gauss_gap / 100, (
        f"marginal-t charged {t_gap:.1f} nats where a fixed-scale Gaussian "
        f"charges {gauss_gap:.0f}; the robustness is not working"
    )


def test_inferred_scale_tracks_residual_size():
    from civsim.uncertainty.sampler import (
        DISCREPANCY_IG_A,
        DISCREPANCY_IG_B,
        SeriesLik,
    )

    tight = SeriesLik("s", np.array([0.5]), n=9, logdet=0.0)
    loose = SeriesLik("s", np.array([50.0]), n=9, logdet=0.0)
    a, b = DISCREPANCY_IG_A, DISCREPANCY_IG_B
    assert tight.posterior_scale(a, b)[0] < loose.posterior_scale(a, b)[0]


def test_inferred_discrepancy_separates_channels(snap):
    """A channel the model fits badly must report a larger scale than one it
    fits well -- otherwise the diagnostic is not measuring anything."""
    from civsim.model import OBSERVED_SERIES, build_engine
    from civsim.uncertainty.priors import sample_prior
    from civsim.uncertainty.sampler import inferred_discrepancy

    h = Holdout(snap, (1950.0, 1990.0), (1990.0, 2020.0), tuple(OBSERVED_SERIES))
    for p in sample_prior(np.random.default_rng(5), 30):
        try:
            traj = build_engine(p, snap, t0=1950.0).run(1950.0, 1990.0)
        except Exception:  # noqa: BLE001
            continue
        break
    paths = {s: traj.series(s)[None, :] for s in OBSERVED_SERIES}
    d = inferred_discrepancy(paths, traj.times, h.calibration(), snap)
    assert set(d) == set(OBSERVED_SERIES)
    assert all(v > 0 for v in d.values())
    assert max(d.values()) > 2 * min(d.values()), (
        "every channel reported the same discrepancy; the estimator is not "
        "distinguishing well-modelled channels from badly modelled ones"
    )


# ------------------------------------------------- rolling origins (M2)


def test_rolling_origins_never_calibrate_on_scored_years(snap):
    from civsim.backtest.rolling import CONTROL_ORIGINS, run_rolling

    with pytest.raises(ValueError, match="before origin"):
        run_rolling(
            origins=(1995.0,), snapshot=snap, fixed_test_start=1975.0,
            n_draws=4, verbose=False,
        )


def test_control_mode_holds_the_test_window_fixed():
    """Origins must differ only in calibration end, or the trend is confounded."""
    from civsim.backtest.rolling import CONTROL_ORIGINS

    assert len(CONTROL_ORIGINS) >= 3
    assert list(CONTROL_ORIGINS) == sorted(CONTROL_ORIGINS)
