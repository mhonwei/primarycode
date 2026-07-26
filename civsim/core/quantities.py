"""Conserved quantities and their canonical units.

A *conserved quantity* is a scalar that the engine tracks across a closed
network of stocks. Every flow moves an amount of exactly one quantity from one
stock to another; nothing is created or destroyed inside the model boundary.
That is the whole point of the kernel: it makes "where did this come from?" a
question the engine can answer mechanically rather than a question the modeller
is trusted to have thought about.

Two of the quantities below are conserved by *physical law*, three by
*accounting identity*. The distinction matters and is recorded explicitly,
because it determines what a conservation violation means:

  - CARBON, ENERGY   -- physical. A violation is a modelling bug, full stop.
  - PERSONS          -- physical (people are not created except by birth).
  - CAPITAL, MONEY   -- accounting. Conserved only because we insist every
                        debit has a credit. A violation means the books do not
                        balance, which is still a bug, but of a different kind:
                        it says the model is asserting a real resource came
                        from nowhere.

See docs/civilization-simulator-design.md §3.2 and §8.
"""

from __future__ import annotations

from enum import Enum


class ConservationBasis(str, Enum):
    """Why a quantity is conserved."""

    PHYSICAL = "physical"
    ACCOUNTING = "accounting"


class Quantity(str, Enum):
    """Conserved quantities tracked by the engine."""

    PERSONS = "persons"
    CARBON = "carbon"
    ENERGY = "energy"
    CAPITAL = "capital"
    MONEY = "money"
    KNOWLEDGE = "knowledge"


CANONICAL_UNIT: dict[Quantity, str] = {
    Quantity.PERSONS: "person",
    Quantity.CARBON: "GtC",
    Quantity.ENERGY: "EJ",
    Quantity.CAPITAL: "G$2011ppp",
    Quantity.MONEY: "G$2011ppp",
    Quantity.KNOWLEDGE: "index",
}

BASIS: dict[Quantity, ConservationBasis] = {
    Quantity.PERSONS: ConservationBasis.PHYSICAL,
    Quantity.CARBON: ConservationBasis.PHYSICAL,
    Quantity.ENERGY: ConservationBasis.PHYSICAL,
    Quantity.CAPITAL: ConservationBasis.ACCOUNTING,
    Quantity.MONEY: ConservationBasis.ACCOUNTING,
    # Knowledge is conserved by accounting convention, not physics. Ideas are
    # not a substance. What the convention buys is that discovery must be drawn
    # from an explicit frontier pool and obsolescence must go somewhere, so
    # "technology improved because the parameter said so" becomes impossible to
    # write. The depleting frontier pool then does real work: it is where the
    # "ideas are getting harder to find" effect lives (Bloom et al. 2020).
    Quantity.KNOWLEDGE: ConservationBasis.ACCOUNTING,
}

# Relative tolerance for the per-step conservation check, by quantity.
# These are tight on purpose: with explicit paired flows, closure should hold to
# floating-point roundoff. A loose tolerance here would silently readmit exactly
# the class of bug the kernel exists to prevent.
DEFAULT_TOLERANCE: dict[Quantity, float] = {
    Quantity.PERSONS: 1e-9,
    Quantity.CARBON: 1e-10,
    Quantity.ENERGY: 1e-10,
    Quantity.CAPITAL: 1e-10,
    Quantity.MONEY: 1e-10,
    Quantity.KNOWLEDGE: 1e-10,
}

# Conversion constant: 1 ppm atmospheric CO2 == 2.124 GtC (IPCC AR6 Table 5.1).
GTC_PER_PPM = 2.124

# 1 GtC == 3.664 GtCO2 (molar mass ratio 44/12).
GTCO2_PER_GTC = 44.0 / 12.0
