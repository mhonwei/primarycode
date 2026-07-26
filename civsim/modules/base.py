"""Module interface.

A module owns some stocks, declares the flows that connect them, and each step
returns the *rate* of each of its flows. It never writes state. Anything a
module wants to expose that is not a stock -- GDP, atmospheric ppm, energy
intensity -- it publishes as a **diagnostic**, which later modules in the same
step can read.

The ordering contract is explicit rather than solved: modules run in the order
they are given to the engine, and a module may only read diagnostics published
by modules ahead of it. This forbids simultaneity by construction. Where the
economics genuinely is simultaneous (output depends on energy, energy demand
depends on output) M0 breaks the loop on the *supply* side -- energy demand is
driven by the capital and labour already in place at the start of the step, not
by output being computed in it -- rather than by lagging a variable a year and
hoping the error is small. See modules/energy.py for why that is defensible.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from ..core.stocks import FlowSpec, StateView, Stock


class Module(ABC):
    #: Unique module name, used to namespace diagnostics in the trajectory.
    name: str = "module"

    @abstractmethod
    def stocks(self) -> list[Stock]:
        """Stocks this module owns. Called once at build time."""

    def flows(self) -> list[FlowSpec]:
        """Flow channels this module owns. Called once at build time."""
        return []

    def diagnostics(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        """Derived values published before rates are computed.

        Runs in module order; may read diagnostics from earlier modules.
        """
        return {}

    def rates(
        self, view: StateView, params: Mapping[str, Any]
    ) -> dict[str, float]:
        """Per-year magnitude of each declared flow, keyed by flow name.

        All diagnostics for the step are available here, including those from
        modules that run later -- rates are computed in a second pass once the
        diagnostic context is complete.
        """
        return {}

    def transactions(
        self, view: StateView, params: Mapping[str, Any]
    ) -> list[tuple[str, str, float, str]]:
        """Financial transactions as (payer, payee, amount, label)."""
        return []
