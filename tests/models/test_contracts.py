# tests/test_contracts.py
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
import pytest

from models.contract import Contract


# ---------- Helpers ----------
def _valid_kwargs(**overrides):
    base = dict(
        client_id=1,
        sales_contact_id=None,
        total_amount=Decimal("1000.00"),
        amount_due=Decimal("400.00"),
        is_signed=False,
    )
    base.update(overrides)
    return base


# ---------- Construction / validation ----------
def test_contract_create_ok():
    c = Contract.create(**_valid_kwargs())
    assert c.client_id == 1
    assert c.sales_contact_id is None
    assert c.total_amount == Decimal("1000.00")
    assert c.amount_due == Decimal("400.00")
    assert c.is_signed is False
    assert isinstance(c.created_at, datetime)
    assert isinstance(c.updated_at, datetime)


@pytest.mark.parametrize(
    "total, due",
    [
        ("-1", "0.00"),          # total négatif
        ("0.00", "-1"),          # due négatif
        ("100.00", "200.00"),    # due > total
    ],
)
def test_invalid_totals_raise(total, due):
    with pytest.raises(ValueError):
        Contract(**_valid_kwargs(total_amount=total, amount_due=due))


@pytest.mark.parametrize(
    "total, due",
    [
        ("1000", "400"),         # str int → ok
        (1000, 400),             # int → ok
        (1000.0, 400.0),         # float → ok (converti)
        (Decimal("1000.00"), Decimal("400.00")),  # Decimal → ok
    ],
)
def test_type_coercion_to_decimal_ok(total, due):
    c = Contract(**_valid_kwargs(total_amount=total, amount_due=due))
    assert c.total_amount == Decimal("1000.00")
    assert c.amount_due == Decimal("400.00")


# ---------- Méthodes métier ----------
def test_touch_updates_updated_at():
    c = Contract.create(**_valid_kwargs())
    before = c.updated_at - timedelta(seconds=1)
    c.updated_at = before
    c.touch()
    assert c.updated_at > before


def test_sign_sets_flag_and_touches():
    c = Contract.create(**_valid_kwargs(is_signed=False))
    before = c.updated_at
    c.sign()
    assert c.is_signed is True
    assert c.updated_at >= before


def test_assign_and_unassign_sales_contact_touch():
    c = Contract.create(**_valid_kwargs(sales_contact_id=None))
    before = c.updated_at
    c.assign_sales_contact(7)
    assert c.sales_contact_id == 7
    assert c.updated_at >= before

    prev = c.updated_at
    c.unassign_sales_contact()
    assert c.sales_contact_id is None
    assert c.updated_at >= prev


def test_update_amounts_ok_and_touches():
    c = Contract.create(**_valid_kwargs(total_amount="1000.00", amount_due="400.00"))
    before = c.updated_at
    c.update_amounts(total_amount="1500.00", amount_due="250.00")
    assert c.total_amount == Decimal("1500.00")
    assert c.amount_due == Decimal("250.00")
    assert c.updated_at >= before


@pytest.mark.parametrize(
    "new_total, new_due",
    [
        ("-10.00", None),            # total négatif
        (None, "-1.00"),             # due négatif
        ("500.00", "600.00"),        # due > total
    ],
)
def test_update_amounts_invalid_raises(new_total, new_due):
    c = Contract.create(**_valid_kwargs())
    with pytest.raises(ValueError):
        c.update_amounts(total_amount=new_total, amount_due=new_due)


def test_record_payment_ok_returns_new_due_and_touches():
    c = Contract.create(**_valid_kwargs(amount_due="400.00"))
    before = c.updated_at
    new_due = c.record_payment("150.00")
    assert new_due == Decimal("250.00")
    assert c.amount_due == Decimal("250.00")
    assert c.updated_at >= before


@pytest.mark.parametrize("amount", ["0.00", "-1.00"])
def test_record_payment_non_positive_raises(amount):
    c = Contract.create(**_valid_kwargs(amount_due="400.00"))
    with pytest.raises(ValueError):
        c.record_payment(amount)


def test_record_payment_greater_than_due_raises():
    c = Contract.create(**_valid_kwargs(amount_due="100.00"))
    with pytest.raises(ValueError):
        c.record_payment("150.00")


# ---------- Sérialisation ----------
def test_to_dict_shape_and_values():
    c = Contract.create(**_valid_kwargs(client_id=42, sales_contact_id=7))
    d = c.to_dict()

    assert {
        "id",
        "client_id",
        "sales_contact_id",
        "total_amount",
        "amount_due",
        "is_signed",
        "created_at",
        "updated_at",
    }.issubset(d.keys())

    assert d["client_id"] == 42
    assert d["sales_contact_id"] == 7
    # sérialisation en str pour les montants
    assert d["total_amount"] == "1000.00"
    assert d["amount_due"] == "400.00"
    assert d["is_signed"] is False
    assert isinstance(d["created_at"], str)
    assert isinstance(d["updated_at"], str)


def test_str_representation():
    c = Contract.create(**_valid_kwargs(client_id=5, amount_due="123.45"))
    s = str(c)
    assert "client=5" in s
    assert "123.45" in s