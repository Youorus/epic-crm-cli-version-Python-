from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Optional

import builtins
import types
import pytest

import cli.services.contracts.update_contract_form as mod
from security.authorization import AuthContext, Role, AuthzError


# ─────────────────────────────────────────────────────────
# Doubles de test
# ─────────────────────────────────────────────────────────

@dataclass
class FakeContract:
    id: int
    client_id: int
    sales_contact_id: Optional[int]
    total_amount: Decimal
    amount_due: Decimal
    is_signed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class FakeService:
    def __init__(self, existing: Optional[FakeContract], *, raise_authz: bool = False):
        self._existing = existing
        self._raise_authz = raise_authz
        self.updated_payload: Optional[FakeContract] = None

    def get(self, contract_id: int, *, auth: AuthContext) -> Optional[FakeContract]:
        if self._raise_authz:
            raise AuthzError("forbidden")
        return self._existing

    def update(self, contract: FakeContract, *, auth: AuthContext) -> Optional[FakeContract]:
        self.updated_payload = contract
        # Émule le “retourne None si introuvable”
        if self._existing is None:
            return None
        return contract


class FakeClientRepoOK:
    """Simule ClientRepo(sess) avec un client existant."""
    def __init__(self, sess):
        pass
    def get(self, client_id: int):
        return object()  # quelque chose de truthy


class FakeClientRepoNone:
    """Simule ClientRepo(sess) sans client (introuvable)."""
    def __init__(self, sess):
        pass
    def get(self, client_id: int):
        return None


@contextmanager
def fake_session_scope():
    yield object()


@pytest.fixture
def auth_gestion() -> AuthContext:
    return AuthContext(user_id=1, role=Role.GESTION)


@pytest.fixture
def existing_contract() -> FakeContract:
    return FakeContract(
        id=5,
        client_id=10,
        sales_contact_id=2,
        total_amount=Decimal("5000.00"),
        amount_due=Decimal("2000.00"),
        is_signed=False,
        created_at=datetime(2025, 8, 11, 12, 0, tzinfo=timezone.utc),
    )


# ─────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────

def test_update_contract_happy_path(monkeypatch, capsys, auth_gestion, existing_contract):
    svc = FakeService(existing_contract)

    # Patch des helpers pour garder le focus sur le flux
    monkeypatch.setattr(mod, "_input_int_optional", lambda prompt: None)  # pas de changement de client/sales
    # On change total et due
    money_answers = iter([Decimal("6000.00"), Decimal("1500.00")])
    monkeypatch.setattr(mod, "_input_money_optional", lambda prompt: next(money_answers))
    # Saisie texte (builtins.input) : ID, signé?, confirmer
    inputs = iter(["5", "o", "o"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))

    # session_scope et ClientRepo ne seront pas utilisés (pas de changement client)
    monkeypatch.setattr(mod, "session_scope", fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", FakeClientRepoOK)

    updated = mod.update_contract_form(service=svc, auth=auth_gestion)

    out = capsys.readouterr().out
    assert updated is not None
    assert "MODIFICATION D’UN CONTRAT" in out
    assert "MODIFICATIONS" in out

    # Vérifie les champs réellement modifiés
    assert updated.total_amount == Decimal("6000.00")
    assert updated.amount_due == Decimal("1500.00")
    assert updated.is_signed is True  # on a entré "o" au prompt
    # Et que l’update a bien reçu cette entité
    assert svc.updated_payload is not None
    assert svc.updated_payload.total_amount == Decimal("6000.00")


def test_update_contract_cancel_on_retour_at_id(monkeypatch, capsys, auth_gestion):
    svc = FakeService(None)
    monkeypatch.setattr(builtins, "input", lambda prompt="": "retour")
    res = mod.update_contract_form(service=svc, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "Opération annulée" in out


def test_update_contract_non_digit_id(monkeypatch, capsys, auth_gestion):
    svc = FakeService(None)
    monkeypatch.setattr(builtins, "input", lambda prompt="": "abc")
    res = mod.update_contract_form(service=svc, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "L’ID doit être un entier" in out


def test_update_contract_not_found_existing(monkeypatch, capsys, auth_gestion):
    svc = FakeService(existing=None)
    # ID correct
    inputs = iter(["5"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    res = mod.update_contract_form(service=svc, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "Contrat introuvable" in out


def test_update_contract_change_client_but_client_missing(monkeypatch, capsys, auth_gestion, existing_contract):
    svc = FakeService(existing_contract)
    # ID → puis signé? (laisser vide, inchangé), puis confirmer n’arrivera pas
    inputs = iter(["5", "", "o"])  # "o" ne sera pas atteint si l’on stoppe avant
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))

    # Forcer un nouveau client_id (ex: 999) → check existence → introuvable
    monkeypatch.setattr(mod, "_input_int_optional", lambda prompt: 999)
    # Montants inchangés
    monkeypatch.setattr(mod, "_input_money_optional", lambda prompt: None)
    # parse_yes_no_optional : on laisse vide donc default=existing.is_signed (False) → pas besoin de patcher

    # session_scope + ClientRepo => simulateur "introuvable"
    monkeypatch.setattr(mod, "session_scope", fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", FakeClientRepoNone)

    res = mod.update_contract_form(service=svc, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "Client introuvable" in out


def test_update_contract_authz_error_on_get(monkeypatch, capsys, auth_gestion):
    svc = FakeService(existing=None, raise_authz=True)
    inputs = iter(["5"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    res = mod.update_contract_form(service=svc, auth=auth_gestion)
    out = capsys.readouterr().out
    assert res is None
    assert "Accès refusé" in out