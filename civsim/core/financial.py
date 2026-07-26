"""Sectoral financial ledger -- the "SFC" in stock-flow consistent.

Physical conservation (carbon, energy) is the easy half. The half that
distinguishes an SFC model from an ordinary system-dynamics model is the
insistence that **every financial asset is some other sector's liability**, so
that net financial assets summed over all sectors is identically zero.

That identity is what stops a model from financing a transition with money that
has no counterpart -- the accounting analogue of the carbon-from-nowhere bug the
:mod:`~civsim.core.ledger` catches. Godley & Lavoie's quadruple-entry
bookkeeping is the reference; this is a deliberately minimal version of it,
sufficient for the M0 single-region closure and structured so that adding a
rest-of-world sector at M3 is a matter of registering one more sector.

Transactions are recorded as (payer, payee, amount). A payment increases the
payee's net financial assets and decreases the payer's by the same amount, so
the sum-to-zero invariant holds by construction and the test verifies that no
code path bypassed :meth:`FinancialLedger.transact`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class SectorBalanceViolation(AssertionError):
    """Raised when net financial assets across sectors fail to sum to zero."""


@dataclass
class Sector:
    name: str
    #: Net financial assets. Positive = net creditor, negative = net debtor.
    net_financial_assets: float = 0.0
    description: str = ""


@dataclass
class Transaction:
    t: float
    payer: str
    payee: str
    amount: float
    label: str = ""


class FinancialLedger:
    """Double-entry ledger over a fixed set of sectors."""

    def __init__(self, sectors: list[Sector], tolerance: float = 1e-9) -> None:
        if not sectors:
            raise ValueError("financial ledger needs at least one sector")
        self._sectors: dict[str, Sector] = {s.name: s for s in sectors}
        self._tolerance = tolerance
        self._journal: list[Transaction] = []
        # Scale reference for the zero-sum test: comparing an absolute residual
        # against zero is meaningless once flows are order 1e5, so we track the
        # largest gross position seen and test the residual relative to it.
        self._scale: float = 1.0

    @property
    def sectors(self) -> dict[str, Sector]:
        return self._sectors

    @property
    def journal(self) -> list[Transaction]:
        return list(self._journal)

    def balance(self, name: str) -> float:
        try:
            return self._sectors[name].net_financial_assets
        except KeyError:
            raise KeyError(
                f"no sector {name!r}; registered: {sorted(self._sectors)}"
            ) from None

    def transact(
        self, t: float, payer: str, payee: str, amount: float, label: str = ""
    ) -> None:
        """Move `amount` of financial claims from payer to payee."""
        if payer == payee:
            raise ValueError(
                f"transaction {label!r}: payer == payee ({payer!r}); "
                "a self-payment is not a transaction"
            )
        if amount < 0:
            raise ValueError(
                f"transaction {label!r}: negative amount {amount!r}. "
                "Reverse payer and payee instead, so direction stays readable "
                "from the declaration."
            )
        for who in (payer, payee):
            if who not in self._sectors:
                raise KeyError(
                    f"no sector {who!r}; registered: {sorted(self._sectors)}"
                )
        self._sectors[payer].net_financial_assets -= amount
        self._sectors[payee].net_financial_assets += amount
        self._journal.append(Transaction(t, payer, payee, amount, label))
        self._scale = max(
            self._scale,
            max(abs(s.net_financial_assets) for s in self._sectors.values()),
        )

    def residual(self) -> float:
        return sum(s.net_financial_assets for s in self._sectors.values())

    def check(self, t: float) -> None:
        resid = self.residual()
        if abs(resid) / max(self._scale, 1e-12) <= self._tolerance:
            return
        detail = ", ".join(
            f"{n}={s.net_financial_assets:.6g}" for n, s in self._sectors.items()
        )
        raise SectorBalanceViolation(
            f"sectoral balances do not sum to zero at t={t:g}: "
            f"residual={resid:.6g} (scale={self._scale:.6g}); {detail}. "
            "Some sector gained a financial asset with no matching liability."
        )
