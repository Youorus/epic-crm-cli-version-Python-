# tests/test_users.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import re
import pytest

from models.users import User
from enums.user_role import UserRole


# ---------- Helpers ----------
VALID_PASSWORD = "Azerty123$!"  # respecte la plupart des politiques usuelles


def test_create_minimal_and_defaults():
    u = User.create(username="john", email="John.Doe@Example.com", role=UserRole.GESTION)
    assert u.id is None
    assert u.username == "john"              # validate_username a pu normaliser/valider
    assert u.email.lower() == "john.doe@example.com"  # normalize_email
    assert u.role == UserRole.GESTION
    assert u.is_active is True
    assert u.is_staff is False
    assert u.is_superuser is False
    assert isinstance(u.created_at, datetime)
    assert isinstance(u.updated_at, datetime)
    assert u.created_at.tzinfo is not None
    assert u.updated_at.tzinfo is not None
    # pas de mot de passe par défaut
    assert u.check_password("anything") is False


def test_create_with_password_sets_hash_and_check_ok():
    u = User.create(username="alice", email="alice@example.com", role="COMMERCIAL", password=VALID_PASSWORD)
    assert u.role == UserRole.COMMERCIAL  # validate_enum accepte str/Enum
    assert u.check_password(VALID_PASSWORD) is True
    assert u.check_password("wrong") is False


def test_set_password_and_clear_password():
    u = User.create(username="bob", email="bob@example.com", role=UserRole.SUPPORT)
    assert u.check_password("x") is False  # rien de défini
    u.set_password(VALID_PASSWORD)
    assert u.check_password(VALID_PASSWORD) is True
    u.clear_password()
    assert u.check_password(VALID_PASSWORD) is False


def test_set_password_rejects_empty_password():
    u = User.create(username="sam", email="sam@example.com", role=UserRole.GESTION)
    with pytest.raises(ValueError):
        u.set_password("")  # la politique doit refuser


def test_touch_updates_updated_at():
    u = User.create(username="tim", email="tim@example.com", role=UserRole.SUPPORT)
    before = u.updated_at - timedelta(seconds=1)  # force une valeur antérieure
    u.updated_at = before
    u.touch()
    assert u.updated_at > before


def test_set_role_accepts_str_and_enum_and_updates_timestamp():
    u = User.create(username="eve", email="eve@example.com", role="SUPPORT")
    before = u.updated_at
    u.set_role(UserRole.GESTION)
    assert u.role == UserRole.GESTION
    assert u.updated_at >= before
    before = u.updated_at
    u.set_role("COMMERCIAL")
    assert u.role == UserRole.COMMERCIAL
    assert u.updated_at >= before


def test_mark_login_sets_last_login_with_timezone_and_updates():
    u = User.create(username="leo", email="leo@example.com", role=UserRole.SUPPORT)
    assert u.last_login is None
    u.mark_login()
    assert isinstance(u.last_login, datetime)
    assert u.last_login.tzinfo is timezone.utc  # converti/forcé en UTC
    # fourni une date custom
    when = datetime(2020, 1, 1, 12, 0, tzinfo=timezone.utc)
    u.mark_login(when=when)
    assert u.last_login == when


def test_to_dict_public_fields():
    u = User.create(username="mike", email="mike@example.com", role="GESTION")
    d = u.to_dict()
    assert d["username"] == "mike"
    assert d["email"] == "mike@example.com"
    assert d["role"] == "GESTION"
    # champs temporels sérialisés en ISO
    assert isinstance(d["date_joined"], str)
    assert isinstance(d["created_at"], str)
    assert isinstance(d["updated_at"], str)
    # secrets absents par défaut
    assert "_password_salt" not in d
    assert "_password_hash" not in d


def test_to_dict_include_private_exposes_hex_strings_when_password_set():
    u = User.create(username="zoe", email="zoe@example.com", role="SUPPORT", password=VALID_PASSWORD)
    d = u.to_dict(include_private=True)
    # présents et sous forme hex
    assert d["_password_salt"] is not None
    assert d["_password_hash"] is not None
    assert re.fullmatch(r"[0-9a-f]+", d["_password_salt"])  # hex
    assert re.fullmatch(r"[0-9a-f]+", d["_password_hash"])


def test_str_contains_username_and_role_value():
    u = User.create(username="ann", email="ann@example.com", role="GESTION")
    s = str(u)
    assert "ann" in s and "GESTION" in s