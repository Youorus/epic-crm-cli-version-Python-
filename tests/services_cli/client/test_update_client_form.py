from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone, date

import pytest

from models.clients import Client
from security.authorization import AuthContext, Role, AuthzError

# Module sous test
import cli.services.clients.update_client_form as mod


# ---------- Helpers ----------
def _client(
    *,
    cid: int = 1,
    full_name: str = "Ada Lovelace",
    email: str = "ada@example.com",
    phone: str = "+33 1 23 45 67 89",
    company: str = "Analytical Engines",
    last: date | None = None,
):
    now = datetime(2025, 1, 2, 10, 30, tzinfo=timezone.utc)
    return Client(
        id=cid,
        full_name=full_name,
        email=email,
        phone=phone,
        company_name=company,
        last_contact=last,
        sales_contact_id=2,
        created_at=now,
        updated_at=now,
    )


class FakeRepo:
    """Repo minimaliste pour monkeypatcher ClientRepo(sess).get(id)."""
    def __init__(self, sess, *, client: Client | None):
        self._client = client

    def get(self, cid: int):
        return self._client


@contextmanager
def _fake_session_scope():
    yield object()


class FakeService:
    def __init__(self, *, updated: Client | None = None, raise_auth=False):
        self.updated_in = None
        self.raise_auth = raise_auth
        self.updated_out = updated

    def update(self, client: Client, *, auth: AuthContext):
        self.updated_in = client
        if self.raise_auth:
            raise AuthzError("forbidden")
        return self.updated_out


def _feed_inputs(monkeypatch, answers: list[str]):
    """Remplace le builtin input() par une séquence prédéfinie."""
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(it))


# ---------- Tests ----------
def test_update_client_happy_path_gestion_changes_name_and_sales_contact(monkeypatch, capsys):
    current = _client()
    # Patch session + repo pour renvoyer le client existant
    monkeypatch.setattr(mod, "session_scope", _fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", lambda s: FakeRepo(s, client=current))

    # Service renvoie l'objet mis à jour (simulateur)
    svc = FakeService(updated=current)
    auth = AuthContext(user_id=99, role=Role.GESTION)

    # Entrées utilisateur :
    # ID, full_name, email(blank), phone(blank), company(blank), last_contact(blank),
    # sales_contact_id=42, confirm='o'
    _feed_inputs(
        monkeypatch,
        ["1", "Ada King", "", "", "", "", "42", "o"],
    )

    result = mod.update_client_form(service=svc, auth=auth)
    out = capsys.readouterr().out

    assert "MODIFICATION D’UN CLIENT" in out
    assert "RÉCAP MODIFICATION" in out
    assert "✅ Client mis à jour." in out
    assert result is current  # le service a renvoyé current
    # Le service a bien reçu un objet édité
    assert svc.updated_in is not None
    assert svc.updated_in.full_name == "Ada King"
    assert svc.updated_in.sales_contact_id == 42


def test_update_client_cancel_on_retour_at_id(monkeypatch, capsys):
    svc = FakeService(updated=None)
    auth = AuthContext(user_id=1, role=Role.GESTION)

    _feed_inputs(monkeypatch, ["retour"])
    result = mod.update_client_form(service=svc, auth=auth)
    out = capsys.readouterr().out

    assert "Opération annulée" in out
    assert result is None


def test_update_client_non_digit_id(monkeypatch, capsys):
    svc = FakeService(updated=None)
    auth = AuthContext(user_id=1, role=Role.GESTION)

    _feed_inputs(monkeypatch, ["abc"])
    result = mod.update_client_form(service=svc, auth=auth)
    out = capsys.readouterr().out

    assert "L’ID doit être un entier" in out
    assert result is None


def test_update_client_not_found(monkeypatch, capsys):
    # Repo renvoie None
    monkeypatch.setattr(mod, "session_scope", _fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", lambda s: FakeRepo(s, client=None))

    svc = FakeService(updated=None)
    auth = AuthContext(user_id=1, role=Role.GESTION)

    _feed_inputs(monkeypatch, ["123"])  # ID
    result = mod.update_client_form(service=svc, auth=auth)
    out = capsys.readouterr().out

    assert "Client introuvable" in out
    assert result is None


def test_update_client_invalid_last_contact_format(monkeypatch, capsys):
    current = _client()
    monkeypatch.setattr(mod, "session_scope", _fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", lambda s: FakeRepo(s, client=current))

    svc = FakeService(updated=None)
    auth = AuthContext(user_id=1, role=Role.GESTION)

    # ID ok, tous champs vides sauf last_contact invalide
    _feed_inputs(monkeypatch, ["1", "", "", "", "", "2025/13/99"])
    result = mod.update_client_form(service=svc, auth=auth)
    out = capsys.readouterr().out

    assert "Format attendu: YYYY-MM-DD" in out
    assert result is None


def test_update_client_invalid_email(monkeypatch, capsys):
    current = _client()
    monkeypatch.setattr(mod, "session_scope", _fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", lambda s: FakeRepo(s, client=current))

    svc = FakeService(updated=None)
    auth = AuthContext(user_id=1, role=Role.GESTION)

    # ID ok, email invalide, autres vides
    _feed_inputs(monkeypatch, ["1", "", "notanemail", "", "", ""])
    result = mod.update_client_form(service=svc, auth=auth)
    out = capsys.readouterr().out

    assert "Email invalide" in out
    assert result is None


def test_update_client_commercial_no_sales_contact_prompt(monkeypatch, capsys):
    current = _client()
    monkeypatch.setattr(mod, "session_scope", _fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", lambda s: FakeRepo(s, client=current))

    svc = FakeService(updated=current)
    auth = AuthContext(user_id=2, role=Role.COMMERCIAL)

    # Séquence d’inputs pour COMMERCIAL (pas de prompt SalesContactID) :
    # ID, full_name(blank), email(blank), phone(blank), company("New Co"),
    # last_contact(blank), confirm('o')
    _feed_inputs(monkeypatch, ["1", "", "", "", "New Co", "", "o"])

    result = mod.update_client_form(service=svc, auth=auth)
    out = capsys.readouterr().out

    assert "✅ Client mis à jour." in out
    assert result is current
    assert svc.updated_in.company_name == "New Co"


def test_update_client_authz_error(monkeypatch, capsys):
    current = _client()
    monkeypatch.setattr(mod, "session_scope", _fake_session_scope)
    monkeypatch.setattr(mod, "ClientRepo", lambda s: FakeRepo(s, client=current))

    svc = FakeService(updated=None, raise_auth=True)
    auth = AuthContext(user_id=3, role=Role.COMMERCIAL)

    # ID, rien ne change, last_contact(blank), confirm
    _feed_inputs(monkeypatch, ["1", "", "", "", "", "", "o"])
    result = mod.update_client_form(service=svc, auth=auth)
    out = capsys.readouterr().out

    assert "Accès refusé" in out
    assert result is None