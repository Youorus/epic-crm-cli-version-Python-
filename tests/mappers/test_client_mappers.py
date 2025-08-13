# tests/mappers/test_client_mappers.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timezone

import pytest

from models.clients import Client
import services.mappers.client_mappers as cm


# Faux ORM model pour isoler le test du vrai SQLAlchemy
@dataclass
class FakeClientModel:
    id: int | None = None
    full_name: str = ""
    email: str = ""
    phone: str = ""
    company_name: str = ""
    last_contact: date | datetime | str | None = None
    sales_contact_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


def test_client_to_entity_handles_various_last_contact_types(monkeypatch):
    # Remplace ClientModel dans le module mappé
    monkeypatch.setattr(cm, "ClientModel", FakeClientModel)

    now = datetime.now(timezone.utc)
    # 1) date
    orm1 = FakeClientModel(
        id=1, full_name="Ada", email="ada@example.com", phone="000",
        company_name="Analytical", last_contact=date(2024, 5, 1),
        created_at=now, updated_at=now
    )
    c1 = cm.client_to_entity(orm1)
    assert c1.last_contact == date(2024, 5, 1)

    # 2) datetime -> .date()
    orm2 = FakeClientModel(
        id=2, full_name="Alan", email="alan@example.com", phone="111",
        company_name="Enigma", last_contact=datetime(2024, 6, 2, 15, 30, tzinfo=timezone.utc),
        created_at=now, updated_at=now
    )
    c2 = cm.client_to_entity(orm2)
    assert c2.last_contact == date(2024, 6, 2)

    # 3) ISO string (date)
    orm3 = FakeClientModel(
        id=3, full_name="Grace", email="grace@example.com", phone="222",
        company_name="COBOL", last_contact="2024-07-03",
        created_at=now, updated_at=now
    )
    c3 = cm.client_to_entity(orm3)
    assert c3.last_contact == date(2024, 7, 3)

    # 4) ISO string (datetime)
    orm4 = FakeClientModel(
        id=4, full_name="Linus", email="linus@example.com", phone="333",
        company_name="Kernel", last_contact="2024-07-04T10:11:12+00:00",
        created_at=now, updated_at=now
    )
    c4 = cm.client_to_entity(orm4)
    assert c4.last_contact == date(2024, 7, 4)


def test_client_to_entity_invalid_last_contact_raises(monkeypatch):
    monkeypatch.setattr(cm, "ClientModel", FakeClientModel)
    orm = FakeClientModel(
        id=9, full_name="Bad", email="bad@example.com", phone="999",
        company_name="Oops", last_contact="not-a-date"
    )
    with pytest.raises(ValueError):
        cm.client_to_entity(orm)


def test_client_new_orm_and_apply(monkeypatch):
    monkeypatch.setattr(cm, "ClientModel", FakeClientModel)

    c = Client.create(
        full_name="Ada Lovelace",
        email="ada@example.com",
        phone="+33 1 23 45 67 89",
        company_name="Analytical Engines",
        last_contact=date(2024, 5, 1),
        sales_contact_id=42,
    )
    orm = cm.client_new_orm(c)
    assert isinstance(orm, FakeClientModel)
    assert orm.full_name == "Ada Lovelace"
    assert orm.last_contact == date(2024, 5, 1)
    assert orm.sales_contact_id == 42

    # apply
    c.update_contact_info(full_name="Ada L.", phone="000")
    cm.client_apply(orm, c)
    assert orm.full_name == "Ada L."
    assert orm.phone == "000"