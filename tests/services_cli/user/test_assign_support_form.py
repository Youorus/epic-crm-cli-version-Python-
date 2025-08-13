from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import builtins
import pytest

import cli.services.events.assign_support_form as mod
from security.authorization import AuthContext, Role, AuthzError



# ─────────────────────────────────────────────────────────
# Doubles de test
# ─────────────────────────────────────────────────────────

@dataclass
class FakeEvent:
    id: int
    contract_id: int
    client_id: int
    support_contact_id: Optional[int]
    event_name: str
    event_start: datetime
    event_end: datetime
    location: str
    attendees: int
    notes: str
    created_at: datetime


@dataclass
class FakeUser:
    id: int
    role: Role  # on utilisera Role.SUPPORT / Role.GESTION pour simplifier


class FakeEventService:
    def __init__(self, ev: Optional[FakeEvent] = None, *, raise_on_get: bool = False, raise_on_update: bool = False):
        self._ev = ev
        self._raise_on_get = raise_on_get
        self._raise_on_update = raise_on_update
        self.updated_with: Optional[FakeEvent] = None

    def get(self, event_id: int, *, auth: AuthContext) -> Optional[FakeEvent]:
        if self._raise_on_get:
            raise AuthzError("forbidden-get")
        return self._ev

    def update(self, event: FakeEvent, *, auth: AuthContext) -> Optional[FakeEvent]:
        if self._raise_on_update:
            raise AuthzError("forbidden-update")
        if self._ev is None:
            return None
        self.updated_with = event
        return event


class FakeUserService:
    def __init__(self, user: Optional[FakeUser]):
        self._user = user

    def get(self, user_id: int, *, auth: AuthContext) -> Optional[FakeUser]:
        return self._user


# ─────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────

@pytest.fixture
def auth_gestion() -> AuthContext:
    return AuthContext(user_id=1, role=Role.GESTION)

@pytest.fixture
def auth_support() -> AuthContext:
    return AuthContext(user_id=2, role=Role.SUPPORT)

@pytest.fixture
def sample_event() -> FakeEvent:
    now = datetime(2025, 8, 11, 12, 0, tzinfo=timezone.utc)
    return FakeEvent(
        id=10,
        contract_id=5,
        client_id=3,
        support_contact_id=None,
        event_name="AG",
        event_start=now,
        event_end=now,
        location="Paris",
        attendees=100,
        notes="",
        created_at=now,
    )


# ─────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────

def test_assign_support_forbidden_role(monkeypatch, capsys, auth_support, sample_event):
    es = FakeEventService(sample_event)
    us = FakeUserService(FakeUser(id=3, role=Role.SUPPORT))
    # Premier prompt → n'importe quoi, on ne doit jamais y arriver (bloqué avant)
    monkeypatch.setattr(builtins, "input", lambda prompt="": "10")
    res = mod.assign_support_to_event_form(event_service=es, user_service=us, auth=auth_support)
    out = capsys.readouterr().out
    assert res is None
    assert "seule la GESTION peut assigner" in out


def test_assign_support_cancel_on_retour_at_event_id(monkeypatch, capsys, auth_gestion, sample_event):
    es = FakeEventService(sample_event)
    us = FakeUserService(FakeUser(id=3, role=Role.SUPPORT))
    # ID → 'retour'
    monkeypatch.setattr(builtins, "input", lambda prompt="": "retour")
    res = mod.assign_support_to_event_form(event_service=es, user_service=us, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "Opération annulée" in out


def test_assign_support_non_digit_event_id(monkeypatch, capsys, auth_gestion, sample_event):
    es = FakeEventService(sample_event)
    us = FakeUserService(FakeUser(id=3, role=Role.SUPPORT))
    inputs = iter(["abc", "10", "3", "o"])  # 1) bad id, 2) ok id, 3) support id, 4) confirm
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    res = mod.assign_support_to_event_form(event_service=es, user_service=us, auth=auth_gestion)
    assert res is not None  # finit par passer
    out = capsys.readouterr().out
    assert "L’ID doit être un entier" in out


def test_assign_support_event_not_found(monkeypatch, capsys, auth_gestion):
    es = FakeEventService(ev=None)
    us = FakeUserService(FakeUser(id=3, role=Role.SUPPORT))
    # ID ok → 10
    inputs = iter(["10"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    res = mod.assign_support_to_event_form(event_service=es, user_service=us, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "Événement introuvable" in out


def test_assign_support_authz_error_on_get(monkeypatch, capsys, auth_gestion):
    es = FakeEventService(ev=None, raise_on_get=True)
    us = FakeUserService(FakeUser(id=3, role=Role.SUPPORT))
    inputs = iter(["10"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    res = mod.assign_support_to_event_form(event_service=es, user_service=us, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "Accès refusé" in out


def test_assign_support_cancel_on_empty_support_id(monkeypatch, capsys, auth_gestion, sample_event):
    es = FakeEventService(sample_event)
    us = FakeUserService(FakeUser(id=3, role=Role.SUPPORT))
    inputs = iter([
        "10",   # event id
        "",     # support id -> annulation
    ])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    res = mod.assign_support_to_event_form(event_service=es, user_service=us, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "Opération annulée" in out


def test_assign_support_non_digit_support_id(monkeypatch, capsys, auth_gestion, sample_event):
    es = FakeEventService(sample_event)
    us = FakeUserService(FakeUser(id=3, role=Role.SUPPORT))
    inputs = iter([
        "10",   # event id
        "xyz",  # bad support id
    ])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    res = mod.assign_support_to_event_form(event_service=es, user_service=us, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "L’ID doit être un entier" in out


def test_assign_support_user_read_forbidden(monkeypatch, capsys, auth_gestion, sample_event):
    es = FakeEventService(sample_event)
    # On va tromper can_read_users pour retourner False
    monkeypatch.setattr(mod, "can_read_users", lambda auth: False)

    us = FakeUserService(FakeUser(id=3, role=Role.SUPPORT))
    inputs = iter(["10", "3"])  # event id ok, support id ok
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))

    res = mod.assign_support_to_event_form(event_service=es, user_service=us, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "Accès refusé pour lire les utilisateurs" in out


def test_assign_support_user_not_found(monkeypatch, capsys, auth_gestion, sample_event):
    es = FakeEventService(sample_event)
    us = FakeUserService(user=None)  # introuvable
    inputs = iter(["10", "3"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    # Laisse can_read_users normal
    res = mod.assign_support_to_event_form(event_service=es, user_service=us, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "Collaborateur introuvable" in out


def test_assign_support_user_wrong_role(monkeypatch, capsys, auth_gestion, sample_event):
    es = FakeEventService(sample_event)
    us = FakeUserService(FakeUser(id=3, role=Role.GESTION))  # pas SUPPORT
    inputs = iter(["10", "3"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    res = mod.assign_support_to_event_form(event_service=es, user_service=us, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "n’a pas le rôle SUPPORT" in out


def test_assign_support_cancel_on_confirm(monkeypatch, capsys, auth_gestion, sample_event):
    es = FakeEventService(sample_event)
    us = FakeUserService(FakeUser(id=3, role=Role.SUPPORT))
    inputs = iter(["10", "3", "n"])  # event id, support id, refuse
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    res = mod.assign_support_to_event_form(event_service=es, user_service=us, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "Assignation annulée" in out


def test_assign_support_happy_path(monkeypatch, capsys, auth_gestion, sample_event):
    es = FakeEventService(sample_event)
    us = FakeUserService(FakeUser(id=3, role=Role.SUPPORT))
    inputs = iter(["10", "3", "o"])  # event id, support id, confirmer
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    res = mod.assign_support_to_event_form(event_service=es, user_service=us, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is not None
    assert "Support #3 assigné" in out
    assert es.updated_with is not None
    assert es.updated_with.support_contact_id == 3


def test_assign_support_authz_error_on_update(monkeypatch, capsys, auth_gestion, sample_event):
    es = FakeEventService(sample_event, raise_on_update=True)
    us = FakeUserService(FakeUser(id=3, role=Role.SUPPORT))
    inputs = iter(["10", "3", "o"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    res = mod.assign_support_to_event_form(event_service=es, user_service=us, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "Accès refusé" in out