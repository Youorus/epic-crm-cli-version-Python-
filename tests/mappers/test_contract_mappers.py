# tests/mappers/test_contract_mappers.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from models.contract import Contract
import services.mappers.contract_mappers as mm


@dataclass
class FakeContractModel:
    id: int | None = None
    client_id: int = 0
    sales_contact_id: int | None = None
    total_amount: object = "0"   # volontairement non typé strict
    amount_due: object = "0"
    is_signed: object = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


def test_contract_to_entity_normalizes_decimals(monkeypatch):
    monkeypatch.setattr(mm, "ContractModel", FakeContractModel)

    now = datetime.now(timezone.utc)
    orm = FakeContractModel(
        id=1, client_id=10, sales_contact_id=20,
        total_amount="1 234,56 €", amount_due="200,00",
        is_signed="1", created_at=now, updated_at=now
    )
    c = mm.contract_to_entity(orm)
    assert isinstance(c.total_amount, Decimal) and c.total_amount == Decimal("1234.56")
    assert isinstance(c.amount_due, Decimal) and c.amount_due == Decimal("200.00")
    assert c.is_signed is True


