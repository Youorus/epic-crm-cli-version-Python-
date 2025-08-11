from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(slots=True)
class Contract:
    # Relations (IDs int)
    client_id: int
    sales_contact_id: Optional[int] = None

    # Données financières
    total_amount: Decimal = field(default=Decimal("0.00"))
    amount_due: Decimal = field(default=Decimal("0.00"))

    # Statut
    is_signed: bool = False

    # Techniques
    id: Optional[int] = None
    created_at: datetime = field(default_factory=_utcnow, kw_only=True)
    updated_at: datetime = field(default_factory=_utcnow, kw_only=True)

    def __post_init__(self) -> None:
        self.total_amount = money_in_range(self.total_amount, field="total_amount", min_=0)
        self.amount_due   = money_in_range(self.amount_due,   field="amount_due",   min_=0)
        validate_due_vs_total(self.amount_due, self.total_amount)

    # Métier
    def touch(self) -> None:
        self.updated_at = _utcnow()

    def sign(self) -> None:
        if not self.is_signed:
            self.is_signed = True
            self.touch()

    def unassign_sales_contact(self) -> None:
        if self.sales_contact_id is not None:
            self.sales_contact_id = None
            self.touch()

    def assign_sales_contact(self, user_id: Optional[int]) -> None:
        if user_id != self.sales_contact_id:
            self.sales_contact_id = user_id
            self.touch()

    def update_amounts(
        self,
        *,
        total_amount: Decimal | int | float | str | None = None,
        amount_due: Decimal | int | float | str | None = None,
    ) -> None:
        new_total = money_in_range(total_amount if total_amount is not None else self.total_amount, field="total_amount", min_=0)
        new_due   = money_in_range(amount_due   if amount_due   is not None else self.amount_due,   field="amount_due",   min_=0)
        validate_due_vs_total(new_due, new_total)
        self.total_amount, self.amount_due = new_total, new_due
        self.touch()

    def record_payment(self, amount: Decimal | int | float | str) -> Decimal:
        payment = money_in_range(amount, field="payment", min_=0)
        if payment <= 0:
            raise ValueError("Le paiement doit être strictement positif.")
        if payment > self.amount_due:
            raise ValueError("Le paiement dépasse le montant dû.")
        self.amount_due = self.amount_due - payment
        # re-quantize via money_in_range pour robustesse
        self.amount_due = money_in_range(self.amount_due, field="amount_due", min_=0)
        self.touch()
        return self.amount_due

    # Sérialisation
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "sales_contact_id": self.sales_contact_id,
            "total_amount": str(self.total_amount),
            "amount_due": str(self.amount_due),
            "is_signed": self.is_signed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def create(
        cls,
        *,
        client_id: int,
        sales_contact_id: Optional[int] = None,
        total_amount: Decimal | int | float | str = "0.00",
        amount_due: Decimal | int | float | str = "0.00",
        is_signed: bool = False,
    ) -> "Contract":
        return cls(
            client_id=client_id,
            sales_contact_id=sales_contact_id,
            total_amount=total_amount,
            amount_due=amount_due,
            is_signed=is_signed,
        )

    def __str__(self) -> str:
        return f"Contrat #{self.id or '∅'} (client={self.client_id}, dû={self.amount_due}€)"