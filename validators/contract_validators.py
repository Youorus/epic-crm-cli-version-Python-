# src/your_app/domain/validators/contract_validators.py
from __future__ import annotations
from decimal import Decimal

from validators.validators  import (
    ValidationError,
    money_in_range,
    validate_due_vs_total,
    q2,
)

def validate_total_amount(value) -> Decimal:
    return money_in_range(value, field="total_amount", min_=0)

def validate_amount_due(value) -> Decimal:
    return money_in_range(value, field="amount_due", min_=0)

def validate_amounts_consistency(amount_due: Decimal, total_amount: Decimal) -> None:
    validate_due_vs_total(amount_due, total_amount)

def validate_payment_amount(value) -> Decimal:
    amt = money_in_range(value, field="payment", min_=0)
    if amt <= q2(0):
        raise ValidationError("Le paiement doit être strictement positif.")
    return amt