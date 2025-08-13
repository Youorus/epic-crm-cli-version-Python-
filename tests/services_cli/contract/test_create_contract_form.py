from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Optional

import pytest

import cli.services.contracts.create_contract_form as mod
from models.contract import Contract
from models.clients import Client
from security.authorization import AuthContext, Role, AuthzError


# ---------- Fakes & helpers ----------

class FakeClientRepo:
    """
    Simule ClientRepo :
      - get(id) : renvoie un Client en mémoire (ou None)
      - update(client) : remplace l'objet en mémoire (capture pour assertions)
    """
    def __init__(self, sess, *, existing_client: Optional[Client]):
        self._client = existing_client
        self.update_called_with: Optional[Client] = None

    def get(self, cid: int) -> Optional[Client]:
        return self._client if (self._client and self._client.id == cid) else None

    def update(self, client: Client) -> Client:
        self._client = client
        self.update_called_with = client
        return client


@contextmanager
def _fake_session_scope():
    # On n'a pas besoin d'un objet session réel : yield un token neutre
    yield object()


class FakeContractService:
    """
    Simule le use-case ContractService :
      - create() renvoie un Contract (ou lève AuthzError si configuré)
    """
    def __init__(self, *, raise_auth: bool = False, created_at: Optional[datetime] = None):
        self.raise_auth = raise_auth
        self.calls = []
        self.created_at = created_at or datetime(2025, 8, 11, 12, 0, tzinfo=timezone.utc)

    def create(self, contract: Contract, *, auth: AuthContext) -> Contract:
        self.calls.append(("create", contract, auth))
        if self.raise_auth:
            raise AuthzError("forbidden")
        # Retourne un objet "persisté" avec un id et created_at défini
        return Contract(
            id=42,
            client_id=contract.client_id,
            sales_contact_id=contract.sales_contact_id,
            total_amount=contract.total_amount,
            amount_due=contract.amount_due,
            is_signed=contract.is_signed,
            created_at=self.created_at,
            updated_at=self.created_at,
        )


def _feed_inputs(monkeypatch, answers: list[str]):
    """
    Séquence d'inputs : remplace builtins.input par un itérateur.
    """
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(it))


def _client_seed(cid: int = 1) -> Client:
    now = datetime(2025, 8, 11, 11, 0, tzinfo=timezone.utc)
    return Client(
        id=cid,
        full_name="Ada Lovelace",
        email="ada@example.com",
        phone="+33 1 23 45 67 89",
        company_name="Analytical Engines",
        last_contact=None,
        sales_contact_id=2,
        created_at=now,
        updated_at=now,
    )


# ---------- Tests ----------

def test_create_contract_happy_path_updates_client_last_contact(monkeypatch, capsys):
    """
    Cas nominal :
      - ID client valide
      - total 5000, due 2000
      - signé = oui
      - sales_contact_id = 3
      - confirmation = o
      -> Contrat créé, et client.last_contact mis à jour à la date de création du contrat.
    """
    # Patch du session_scope + ClientRepo
    client = _client_seed(1)
    repo = FakeClientRepo(None, existing_client=client)
    monkeypatch.setattr(mod, "session_scope", _fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", lambda s: repo)

    # Service factice
    created_at = datetime(2025, 8, 12, 10, 30, tzinfo=timezone.utc)
    service = FakeContractService(created_at=created_at)

    auth = AuthContext(user_id=99, role=Role.GESTION)

    # Inputs : client_id, total, due, signé(o), sales_contact(3), confirmer(o)
    _feed_inputs(
        monkeypatch,
        ["1", "5000", "2000", "o", "3", "o"]
    )

    result = mod.create_contract_form(service=service, auth=auth)
    out = capsys.readouterr().out

    assert result is not None
    assert result.id == 42
    assert "Contrat #42 créé avec succès" in out

    # Vérifie que repo.update(client) a été appelé et que last_contact a été posé
    assert repo.update_called_with is not None
    # _as_utc_date(created_at) -> created_at.date()
    assert repo.update_called_with.last_contact == created_at.date()


def test_create_contract_cancel_on_retour_at_client_id(monkeypatch, capsys):
    auth = AuthContext(user_id=1, role=Role.GESTION)
    service = FakeContractService()

    _feed_inputs(monkeypatch, ["retour"])
    result = mod.create_contract_form(service=service, auth=auth)
    out = capsys.readouterr().out

    assert result is None
    assert "Création annulée" in out


def test_create_contract_non_digit_client_then_retour(monkeypatch, capsys):
    """
    L'utilisateur tape un ID non entier → message d'erreur,
    puis "retour" pour annuler.
    """
    auth = AuthContext(user_id=1, role=Role.GESTION)
    service = FakeContractService()

    # Patch repo pour l'appel d'existence (il ne sera pas atteint si on annule)
    monkeypatch.setattr(mod, "session_scope", _fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", lambda s: FakeClientRepo(s, existing_client=_client_seed(1)))

    _feed_inputs(monkeypatch, ["abc", "retour"])
    result = mod.create_contract_form(service=service, auth=auth)
    out = capsys.readouterr().out

    assert result is None
    assert "La valeur doit être un entier" in out
    assert "Création annulée" in out


def test_create_contract_amount_due_cannot_exceed_total(monkeypatch, capsys):
    """
    due > total → message, re-saisie du due, puis confirmation ok.
    """
    client = _client_seed(1)
    repo = FakeClientRepo(None, existing_client=client)
    monkeypatch.setattr(mod, "session_scope", _fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", lambda s: repo)

    service = FakeContractService()
    auth = AuthContext(user_id=1, role=Role.GESTION)

    # Séquence:
    # id=1, total=1000, due=2000 (-> rejoue), due=500, signé=o, sales_contact="" (ignore), confirm=o
    _feed_inputs(monkeypatch, ["1", "1000", "2000", "500", "o", "", "o"])
    result = mod.create_contract_form(service=service, auth=auth)
    out = capsys.readouterr().out

    assert result is not None
    assert "ne peut pas dépasser le montant total" in out
    assert repo.update_called_with is not None  # last_contact mis à jour
    assert repo.update_called_with.last_contact is not None


def test_create_contract_ignores_non_digit_sales_contact(monkeypatch, capsys):
    client = _client_seed(1)
    repo = FakeClientRepo(None, existing_client=client)
    monkeypatch.setattr(mod, "session_scope", _fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", lambda s: repo)

    service = FakeContractService()
    auth = AuthContext(user_id=1, role=Role.GESTION)

    # sales_contact = "abc" -> ignoré
    _feed_inputs(monkeypatch, ["1", "1000", "100", "n", "abc", "o"])
    result = mod.create_contract_form(service=service, auth=auth)
    out = capsys.readouterr().out

    assert result is not None
    assert "ID commercial ignoré" in out
    # Contrat créé malgré tout
    assert result.total_amount == Decimal("1000.00")
    assert result.amount_due == Decimal("100.00")


def test_create_contract_cancel_on_final_confirm(monkeypatch, capsys):
    client = _client_seed(1)
    repo = FakeClientRepo(None, existing_client=client)
    monkeypatch.setattr(mod, "session_scope", _fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", lambda s: repo)

    service = FakeContractService()
    auth = AuthContext(user_id=1, role=Role.GESTION)

    # Tout saisi, mais confirmation ≠ "o"
    _feed_inputs(monkeypatch, ["1", "500", "100", "n", "", "N"])
    result = mod.create_contract_form(service=service, auth=auth)
    out = capsys.readouterr().out

    assert result is None
    assert "Création annulée" in out


def test_create_contract_authz_error(monkeypatch, capsys):
    client = _client_seed(1)
    repo = FakeClientRepo(None, existing_client=client)
    monkeypatch.setattr(mod, "session_scope", _fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", lambda s: repo)

    # Service qui lève une AuthzError
    service = FakeContractService(raise_auth=True)
    auth = AuthContext(user_id=2, role=Role.GESTION)

    _feed_inputs(monkeypatch, ["1", "1000", "100", "o", "", "o"])
    result = mod.create_contract_form(service=service, auth=auth)
    out = capsys.readouterr().out

    assert result is None
    assert "Accès refusé" in out