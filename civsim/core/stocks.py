"""Stocks and flows -- the two primitives of the SFC kernel.

The discipline enforced here is narrow but load-bearing:

  1. A stock holds an amount of exactly one conserved quantity.
  2. A flow moves an amount of exactly one quantity from a named source stock
     to a named sink stock. There is no such thing as a flow with no source.
  3. Modules never write stock values. They return *rates*; the engine applies
     them. Modules see state through a read-only view.

Rule 3 is what makes rule 2 unbypassable. Without it a module could simply
assign `population.value = ...` and the conservation check would pass while the
model quietly manufactured people.

A "boundary" stock is how the model represents the outside world: unextracted
fossil carbon, the pool of the not-yet-born, dissipated waste heat. Boundary
stocks are ordinary stocks in every respect -- they are counted in the
conservation totals -- they are just not things we report on. Making them
explicit is what turns "emissions appear from nowhere" into "emissions are a
transfer out of a finite reserve", which is the constraint that does the real
work in §3.2 of the design.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .quantities import CANONICAL_UNIT, Quantity


class StockKind(str, Enum):
    ACTIVE = "active"
    BOUNDARY = "boundary"


@dataclass
class Stock:
    """A quantity of something, held somewhere.

    `value` is mutated only by :class:`~civsim.core.engine.Engine`. Modules
    receive a :class:`StateView` instead.
    """

    name: str
    quantity: Quantity
    initial: float
    kind: StockKind = StockKind.ACTIVE
    description: str = ""
    #: If False, the engine raises when a flow would drive this stock negative.
    allow_negative: bool = False

    value: float = field(init=False)

    def __post_init__(self) -> None:
        self.value = float(self.initial)

    @property
    def unit(self) -> str:
        return CANONICAL_UNIT[self.quantity]

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Stock({self.name}={self.value:.6g} {self.unit})"


@dataclass(frozen=True)
class FlowSpec:
    """A declared channel between two stocks of the same quantity.

    The spec is static; the per-step magnitude is supplied by the owning
    module's :meth:`~civsim.modules.base.Module.rates`. A positive rate moves
    quantity source -> sink. Negative rates are rejected: if a channel can run
    both ways, declare two flows. This keeps the direction of every transfer
    readable from the model's declaration rather than from its runtime values.
    """

    name: str
    quantity: Quantity
    source: str
    sink: str
    description: str = ""

    def __post_init__(self) -> None:
        if self.source == self.sink:
            raise ValueError(
                f"flow {self.name!r} has source == sink ({self.source!r}); "
                "a flow must move quantity between two distinct stocks"
            )


class StateView:
    """Read-only access to stock values, handed to modules each step.

    Also carries the per-step diagnostic context so that a module can read
    values published by modules that ran earlier in the same step (see
    `Engine.step` for the ordering contract).
    """

    __slots__ = ("_stocks", "_diagnostics", "_t")

    def __init__(
        self,
        stocks: dict[str, Stock],
        diagnostics: dict[str, float],
        t: float,
    ) -> None:
        self._stocks = stocks
        self._diagnostics = diagnostics
        self._t = t

    @property
    def t(self) -> float:
        return self._t

    def stock(self, name: str) -> float:
        try:
            return self._stocks[name].value
        except KeyError:
            raise KeyError(
                f"no stock named {name!r}; declared stocks: "
                f"{sorted(self._stocks)}"
            ) from None

    def diag(self, name: str) -> float:
        """Read a diagnostic published earlier in this same step."""
        try:
            return self._diagnostics[name]
        except KeyError:
            raise KeyError(
                f"diagnostic {name!r} is not available at this point in the "
                f"step. Available: {sorted(self._diagnostics)}. If this is a "
                "genuine dependency, the publishing module must run earlier in "
                "the module order."
            ) from None

    def has_diag(self, name: str) -> bool:
        return name in self._diagnostics
