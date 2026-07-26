"""The kernel's guarantees, tested by trying to break them.

A conservation check that has never been shown to fail is not evidence of
anything. Each test here constructs a module that commits a specific sin and
asserts the engine refuses it.
"""

from __future__ import annotations

import numpy as np
import pytest

from civsim.core.engine import Engine, NegativeStockError
from civsim.core.ledger import ConservationViolation
from civsim.core.quantities import Quantity
from civsim.core.stocks import FlowSpec, Stock, StockKind
from civsim.data.registry import Snapshot
from civsim.model import build_engine
from civsim.modules.base import Module
from civsim.uncertainty.priors import sample_prior


@pytest.fixture(scope="module")
def snapshot():
    return Snapshot()


@pytest.fixture(scope="module")
def params():
    return sample_prior(np.random.default_rng(7), 1)[0]


# --------------------------------------------------------- the real model


def test_full_model_conserves_every_quantity(params, snapshot):
    eng = build_engine(params, snapshot, t0=1950.0)
    eng.run(1950.0, 2020.0)
    for b in eng.ledger.balances():
        assert b.ok, (
            f"{b.quantity.value} drifted: rel_err {b.rel_error:.3e} "
            f"> tol {b.tolerance:.1e}"
        )


def test_conservation_holds_across_many_prior_draws(snapshot):
    for p in sample_prior(np.random.default_rng(11), 12):
        eng = build_engine(p, snapshot, t0=1950.0)
        eng.run(1950.0, 2020.0)
        assert all(b.ok for b in eng.ledger.balances())


def test_carbon_moves_out_of_reserves_not_out_of_nothing(params, snapshot):
    eng = build_engine(params, snapshot, t0=1950.0)
    traj = eng.run(1950.0, 2020.0)
    reserves = traj.stocks["fossil_carbon_reserves"]
    atmos = traj.stocks["atmosphere_c"]
    assert reserves[-1] < reserves[0], "emissions did not deplete the reserve"
    total = sum(
        traj.stocks[n][0]
        for n in ("fossil_carbon_reserves", "atmosphere_c", "ocean_c", "biosphere_c")
    )
    total_end = sum(
        traj.stocks[n][-1]
        for n in ("fossil_carbon_reserves", "atmosphere_c", "ocean_c", "biosphere_c")
    )
    assert abs(total_end - total) / total < 1e-12
    assert atmos[-1] > atmos[0]


def test_energy_extraction_depletes_reserves(params, snapshot):
    eng = build_engine(params, snapshot, t0=1950.0)
    traj = eng.run(1950.0, 2020.0)
    drawn = traj.stocks["energy_reserves"][0] - traj.stocks["energy_reserves"][-1]
    dissipated = traj.stocks["dissipated_heat"][-1]
    assert drawn > 0
    assert abs(drawn - dissipated) / drawn < 1e-12


# ------------------------------------------------------- deliberate sins


class _Cheater(Module):
    """Writes a stock directly instead of declaring a flow."""

    name = "cheater"

    def stocks(self):
        return [Stock("pot", Quantity.CARBON, 100.0)]

    def diagnostics(self, view, params):
        # Reach through the read-only view and mutate the underlying object.
        view._stocks["pot"].value += 1.0  # noqa: SLF001 - that is the point
        return {}


def test_direct_stock_mutation_is_caught():
    eng = Engine([_Cheater()], params={})
    with pytest.raises(ConservationViolation, match="conservation violated"):
        eng.run(0.0, 3.0)


class _DanglingFlow(Module):
    name = "dangling"

    def stocks(self):
        return [Stock("a", Quantity.CARBON, 10.0)]

    def flows(self):
        return [FlowSpec("f", Quantity.CARBON, "a", "nowhere")]


def test_flow_to_undeclared_stock_is_rejected_at_build():
    with pytest.raises(ValueError, match="not a declared stock"):
        Engine([_DanglingFlow()], params={})


class _CrossQuantity(Module):
    name = "cross"

    def stocks(self):
        return [
            Stock("c", Quantity.CARBON, 10.0),
            Stock("e", Quantity.ENERGY, 10.0),
        ]

    def flows(self):
        return [FlowSpec("f", Quantity.CARBON, "c", "e")]


def test_flow_across_quantity_networks_is_rejected():
    with pytest.raises(ValueError, match="may not cross quantity networks"):
        Engine([_CrossQuantity()], params={})


class _NegativeRate(Module):
    name = "negrate"

    def stocks(self):
        return [
            Stock("a", Quantity.CARBON, 10.0),
            Stock("b", Quantity.CARBON, 10.0),
        ]

    def flows(self):
        return [FlowSpec("f", Quantity.CARBON, "a", "b")]

    def rates(self, view, params):
        return {"f": -1.0}


def test_negative_flow_rate_is_rejected():
    eng = Engine([_NegativeRate()], params={})
    with pytest.raises(ValueError, match="negative rate"):
        eng.step(0.0)


class _Overdraw(Module):
    name = "overdraw"

    def stocks(self):
        return [
            Stock("small", Quantity.CARBON, 1.0),
            Stock("big", Quantity.CARBON, 0.0, kind=StockKind.BOUNDARY),
        ]

    def flows(self):
        return [FlowSpec("drain", Quantity.CARBON, "small", "big")]

    def rates(self, view, params):
        return {"drain": 5.0}


def test_drawing_more_than_exists_raises():
    eng = Engine([_Overdraw()], params={})
    with pytest.raises(NegativeStockError, match="would go negative"):
        eng.step(0.0)


class _SelfFlow(Module):
    name = "selfflow"

    def stocks(self):
        return [Stock("a", Quantity.CARBON, 1.0)]

    def flows(self):
        return [FlowSpec("f", Quantity.CARBON, "a", "a")]


def test_self_flow_is_rejected():
    with pytest.raises(ValueError, match="source == sink"):
        _SelfFlow().flows()


# ------------------------------------------------------- ordering contract


class _ReadsFuture(Module):
    name = "reads_future"

    def stocks(self):
        return [Stock("x", Quantity.CARBON, 1.0)]

    def diagnostics(self, view, params):
        return {"needs": view.diag("published_later")}


class _PublishesLater(Module):
    name = "publishes_later"

    def stocks(self):
        return [Stock("y", Quantity.CARBON, 1.0)]

    def diagnostics(self, view, params):
        return {"published_later": 1.0}


def test_reading_a_later_modules_diagnostic_fails_loudly():
    eng = Engine([_ReadsFuture(), _PublishesLater()], params={})
    with pytest.raises(KeyError, match="must run earlier"):
        eng.step(0.0)


def test_module_order_does_not_change_results(params, snapshot):
    """Rates are computed against start-of-step state, so ordering only
    controls information availability, never the arithmetic."""
    a = build_engine(params, snapshot, t0=1950.0).run(1950.0, 2000.0)
    b = build_engine(params, snapshot, t0=1950.0).run(1950.0, 2000.0)
    for k in a.stocks:
        np.testing.assert_allclose(a.stocks[k], b.stocks[k], rtol=0, atol=0)
