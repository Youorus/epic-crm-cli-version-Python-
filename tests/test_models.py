# tests/orm/test_models.py
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from orm.models import Base, UserModel, ClientModel, ContractModel, EventModel


# ─────────────────────────────────────────────────────────
# Fixtures DB (SQLite mémoire + FK ON)
# ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def engine() -> Engine:
    eng = create_engine("sqlite:///:memory:", future=True)

    # Activer les FK SQLite (sinon CASCADE/ON DELETE ignorés)
    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_con, con_record):  # pragma: no cover - hook
        cur = dbapi_con.cursor()
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.close()

    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def session(engine: Engine):
    with Session(engine) as s:
        yield s
        s.rollback()  # isolation test → rollback par défaut


# ─────────────────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────────────────

def test_user_insert_and_uniques(session: Session):
    u1 = UserModel(
        username="alice",
        email="alice@example.com",
        role="GESTION",
        is_active=True,
        is_staff=False,
        is_superuser=False,
    )
    session.add(u1)
    session.commit()
    session.refresh(u1)

    assert u1.id is not None
    assert u1.created_at is not None
    assert u1.updated_at is not None
    assert u1.date_joined is not None

    # Unicité email
    u2 = UserModel(
        username="alice2",
        email="alice@example.com",  # même email → unique
        role="SUPPORT",
    )
    session.add(u2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


# ─────────────────────────────────────────────────────────
# Clients
# ─────────────────────────────────────────────────────────

def test_client_insert_with_sales_contact_and_date(session: Session):
    # user référencé comme sales_contact
    u = UserModel(username="bob", email="bob@example.com", role="COMMERCIAL")
    session.add(u)
    session.commit()

    c = ClientModel(
        full_name="Ada Lovelace",
        email="ada@example.com",
        phone="+33 1 23 45 67 89",
        company_name="Analytical Engines",
        last_contact=date(2024, 1, 2),
        sales_contact_id=u.id,
    )
    session.add(c)
    session.commit()
    session.refresh(c)

    assert c.id is not None
    assert c.sales_contact_id == u.id
    assert isinstance(c.last_contact, (date, type(None)))
    assert c.created_at is not None
    assert c.updated_at is not None

    # Unicité email clients
    dup = ClientModel(
        full_name="Ada L.",
        email="ada@example.com",
        phone="000",
        company_name="Dup",
    )
    session.add(dup)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


# ─────────────────────────────────────────────────────────
# Contracts
# ─────────────────────────────────────────────────────────

def test_contract_decimal_and_checks(session: Session):
    # Pré-req: client + (optionnel) sales user
    user = UserModel(username="sales1", email="sales1@example.com", role="COMMERCIAL")
    client = ClientModel(
        full_name="Grace Hopper",
        email="grace@example.com",
        phone="0600000000",
        company_name="COBOL Inc.",
    )
    session.add_all([user, client])
    session.commit()

    # Insert valide : Numeric(asdecimal=True) → Decimal
    ct = ContractModel(
        client_id=client.id,
        sales_contact_id=user.id,
        total_amount=Decimal("12000.00"),
        amount_due=Decimal("8000.00"),
        is_signed=True,
    )
    session.add(ct)
    session.commit()
    session.refresh(ct)

    assert isinstance(ct.total_amount, Decimal)
    assert isinstance(ct.amount_due, Decimal)
    assert ct.total_amount == Decimal("12000.00")
    assert ct.amount_due == Decimal("8000.00")

    # Check constraints (>= 0)
    bad_neg_total = ContractModel(
        client_id=client.id,
        total_amount=Decimal("-1.00"),
        amount_due=Decimal("0.00"),
        is_signed=False,
    )
    session.add(bad_neg_total)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    bad_neg_due = ContractModel(
        client_id=client.id,
        total_amount=Decimal("10.00"),
        amount_due=Decimal("-0.01"),
        is_signed=False,
    )
    session.add(bad_neg_due)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


# ─────────────────────────────────────────────────────────
# Events
# ─────────────────────────────────────────────────────────

def test_event_unique_contract_and_attendees_check(session: Session):
    # Pré-req: client + contrat
    user = UserModel(username="support", email="support@example.com", role="SUPPORT")
    client = ClientModel(
        full_name="Alan Turing",
        email="alan@example.com",
        phone="0700000000",
        company_name="Enigma Ltd",
    )
    session.add_all([user, client])
    session.commit()

    contract = ContractModel(
        client_id=client.id,
        total_amount=Decimal("5000.00"),
        amount_due=Decimal("2000.00"),
        is_signed=True,
    )
    session.add(contract)
    session.commit()

    # Event OK
    ev = EventModel(
        contract_id=contract.id,
        client_id=client.id,
        support_contact_id=user.id,
        event_name="Conférence",
        event_start=datetime.utcnow(),
        event_end=datetime.utcnow(),
        location="Londres",
        attendees=100,
        notes="—",
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)

    assert ev.id is not None
    assert ev.attendees == 100

    # Unicité contract_id (unique=True)
    ev2 = EventModel(
        contract_id=contract.id,  # même contrat → doit casser
        client_id=client.id,
        event_name="Conf bis",
        event_start=datetime.utcnow(),
        event_end=datetime.utcnow(),
        location="Londres",
        attendees=10,
        notes="dup",
    )
    session.add(ev2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    # Check attendees >= 1
    bad_att = EventModel(
        contract_id=contract.id + 1,  # autre contrat requis
        client_id=client.id,
        event_name="Bad",
        event_start=datetime.utcnow(),
        event_end=datetime.utcnow(),
        location="X",
        attendees=0,  # viole la contrainte
        notes="x",
    )
    # Créer le contrat manquant pour la FK
    c2 = ContractModel(
        client_id=client.id,
        total_amount=Decimal("1.00"),
        amount_due=Decimal("0.00"),
        is_signed=True,
    )
    session.add(c2)
    session.commit()

    bad_att.contract_id = c2.id
    session.add(bad_att)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

