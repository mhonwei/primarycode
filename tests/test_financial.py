"""Sectoral balances must sum to zero -- the accounting half of SFC."""

from __future__ import annotations

import numpy as np
import pytest

from civsim.core.financial import (
    FinancialLedger,
    Sector,
    SectorBalanceViolation,
)
from civsim.data.registry import Snapshot
from civsim.model import build_engine
from civsim.uncertainty.priors import sample_prior


@pytest.fixture
def ledger():
    return FinancialLedger(
        [Sector("households"), Sector("firms"), Sector("government")]
    )


def test_transactions_keep_balances_summing_to_zero(ledger):
    ledger.transact(0.0, "firms", "households", 100.0, "wages")
    ledger.transact(0.0, "households", "government", 20.0, "tax")
    ledger.check(0.0)
    assert ledger.residual() == pytest.approx(0.0)
    assert ledger.balance("households") == pytest.approx(80.0)
    assert ledger.balance("firms") == pytest.approx(-100.0)
    assert ledger.balance("government") == pytest.approx(20.0)


def test_an_asset_without_a_liability_is_caught(ledger):
    # Bypass transact() -- the only way to create an unbalanced position.
    ledger.sectors["households"].net_financial_assets += 50.0
    with pytest.raises(SectorBalanceViolation, match="no matching liability"):
        ledger.check(0.0)


def test_negative_amounts_rejected(ledger):
    with pytest.raises(ValueError, match="negative amount"):
        ledger.transact(0.0, "firms", "households", -5.0, "backwards")


def test_self_payment_rejected(ledger):
    with pytest.raises(ValueError, match="payer == payee"):
        ledger.transact(0.0, "firms", "firms", 5.0, "nonsense")


def test_unknown_sector_rejected(ledger):
    with pytest.raises(KeyError, match="no sector"):
        ledger.transact(0.0, "firms", "martians", 5.0, "x")


def test_full_model_keeps_books_balanced():
    snap = Snapshot()
    # Take the first draw that integrates. Some prior draws legitimately fail --
    # a draw whose emissions exhaust 4000 GtC of fossil reserves inside seventy
    # years is the kernel refusing an impossible world, which is the behaviour
    # tests/test_conservation.py asserts on purpose. This test is about the
    # books balancing, so it needs a world that exists.
    eng = None
    for p in sample_prior(np.random.default_rng(3), 30):
        candidate = build_engine(p, snap, t0=1950.0)
        try:
            candidate.run(1950.0, 2020.0)
        except Exception:  # noqa: BLE001 - any failed draw is simply skipped
            continue
        eng = candidate
        break
    assert eng is not None, "no prior draw integrated; the prior is broken"
    eng.financial.check(2020.0)
    assert abs(eng.financial.residual()) < 1e-6
    # And the circuit actually moved money, so the check is not vacuous.
    assert len(eng.financial.journal) > 200
    assert any(t.label.endswith("wages") for t in eng.financial.journal)
