# tests/test_clients.py
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import pytest

from models.clients import Client


# ---------- Helpers ----------
def _valid_client_kwargs():
    return dict(
        full_name="Ada Lovelace",
        email="ada@example.com",
        phone="+33 1 23 45 67 89",
        company_name="Analytical Engines",
    )


# ---------- Construction / validation ----------
def test_client_create_ok():
    c = Client.create(**_valid_client_kwargs())
    assert c.full_name == "Ada Lovelace"
    assert c.email == "ada@example.com"
    assert c.phone.startswith("+33")
    assert c.company_name == "Analytical Engines"
    assert c.last_contact is None
    assert c.sales_contact_id is None
    assert c.id is None
    # created_at / updated_at sont initialisés (timezone aware)
    assert isinstance(c.created_at, datetime)
    assert isinstance(c.updated_at, datetime)
    assert c.created_at.tzinfo is not None
    assert c.updated_at.tzinfo is not None


@pytest.mark.parametrize(
    "field, value",
    [
        ("full_name", ""),           # nom vide
        ("email", "not-an-email"),   # email invalide
        ("phone", ""),               # téléphone vide
        ("company_name", ""),        # société vide
    ],
)
def test_client_post_init_validation_errors(field, value):
    kwargs = _valid_client_kwargs()
    kwargs[field] = value
    with pytest.raises(ValueError):
        Client(**kwargs)  # __post_init__ doit valider et lever


def test_client_last_contact_validated_when_provided():
    kwargs = _valid_client_kwargs()
    kwargs["last_contact"] = date.today()
    c = Client(**kwargs)
    assert isinstance(c.last_contact, date)


# ---------- Méthodes métier ----------
def test_touch_updates_updated_at():
    c = Client.create(**_valid_client_kwargs())
    before = c.updated_at
    # s'assurer que le temps “avance” visiblement
    c.updated_at = before - timedelta(seconds=1)
    c.touch()
    assert c.updated_at > before - timedelta(seconds=1)


def test_assign_sales_contact_sets_and_touches():
    c = Client.create(**_valid_client_kwargs())
    before = c.updated_at
    c.assign_sales_contact(42)
    assert c.sales_contact_id == 42
    assert c.updated_at >= before


def test_record_contact_default_sets_today():
    c = Client.create(**_valid_client_kwargs())
    c.record_contact()  # sans argument -> aujourd’hui
    assert c.last_contact == date.today()


def test_record_contact_custom_date():
    c = Client.create(**_valid_client_kwargs())
    d = date(2020, 1, 15)
    c.record_contact(d)
    assert c.last_contact == d


def test_update_contact_info_updates_and_validates():
    c = Client.create(**_valid_client_kwargs())
    before = c.updated_at

    c.update_contact_info(
        full_name="Ada L.",
        email="ada.l@example.com",
        phone="+33 6 00 00 00 00",
        company_name="Analytical Engines Ltd",
    )

    assert c.full_name == "Ada L."
    assert c.email == "ada.l@example.com"
    assert c.phone.startswith("+33")
    assert c.company_name == "Analytical Engines Ltd"
    assert c.updated_at >= before


@pytest.mark.parametrize(
    "kwargs, field_expected",
    [
        (dict(full_name=""), "full_name"),
        (dict(email="bad"), "email"),
        (dict(phone=""), "phone"),
        (dict(company_name=""), "company_name"),
    ],
)
def test_update_contact_info_invalid_raises(kwargs, field_expected):
    c = Client.create(**_valid_client_kwargs())
    with pytest.raises(ValueError):
        c.update_contact_info(**kwargs)


# ---------- Sérialisation ----------
def test_to_dict_shape_and_values():
    c = Client.create(**_valid_client_kwargs())
    c.assign_sales_contact(7)
    c.record_contact(date(2024, 2, 3))

    d = c.to_dict()
    # Clés de base
    assert {
        "id",
        "full_name",
        "email",
        "phone",
        "company_name",
        "last_contact",
        "sales_contact_id",
        "created_at",
        "updated_at",
    }.issubset(d.keys())

    # Types/valeurs attendues
    assert d["full_name"] == "Ada Lovelace"
    assert d["email"] == "ada@example.com"
    assert d["phone"].startswith("+33")
    assert d["company_name"] == "Analytical Engines"
    assert d["sales_contact_id"] == 7
    # dates sérialisées en ISO
    assert d["last_contact"] == "2024-02-03"
    assert isinstance(d["created_at"], str)
    assert isinstance(d["updated_at"], str)