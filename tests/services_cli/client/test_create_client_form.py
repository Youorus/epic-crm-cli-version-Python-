# tests/cli/forms/test_create_client_form.py
from __future__ import annotations

import types
import pytest

from security.authorization import AuthContext, Role, AuthzError

# On importe le module qui contient la fonction testée
import cli.services.clients.create_client_form as form_mod
from models.clients import Client


class FakeService:
    """Service factice pour capturer l'appel à create()."""
    def __init__(self, raise_auth=False):
        self.raise_auth = raise_auth
        self.last_client: Client | None = None
        self.called = False

    def create(self, client: Client, *, auth: AuthContext) -> Client:
        self.called = True
        if self.raise_auth:
            raise AuthzError("forbidden")
        # Simule un ID assigné par la DB
        client.id = 123
        self.last_client = client
        return client


def _patch_inputs(monkeypatch, *, req_values, opt_value="", confirm=True):
    """
    Patch les helpers d'I/O dans le module testé.

    req_values : liste des valeurs renvoyées par _req_str
                 (full_name, email, phone, company_name)
    opt_value  : valeur renvoyée par _opt_str (ID commercial pour GESTION)
    confirm    : bool renvoyé par _confirm
    """
    req_iter = iter(req_values)

    def fake_req(prompt: str):
        try:
            return next(req_iter)
        except StopIteration:
            return None

    def fake_opt(prompt: str):
        return opt_value

    def fake_confirm(prompt: str):
        return confirm

    monkeypatch.setattr(form_mod, "_req_str", fake_req)
    monkeypatch.setattr(form_mod, "_opt_str", fake_opt)
    monkeypatch.setattr(form_mod, "_confirm", fake_confirm)


def test_create_client_as_commercial_auto_assign(monkeypatch):
    """Un COMMERCIAL doit être auto-assigné comme sales_contact_id."""
    _patch_inputs(
        monkeypatch,
        req_values=["Ada Lovelace", "ada@example.com", "+33 1 23 45 67 89", "Analytical Engines"],
        confirm=True,
    )
    service = FakeService()
    auth = AuthContext(user_id=42, role=Role.COMMERCIAL)

    created = form_mod.create_client_form(service=service, auth=auth)

    assert service.called is True
    assert created is not None
    assert created.id == 123
    assert created.sales_contact_id == 42  # auto-assignation


def test_create_client_as_gestion_with_explicit_sales_contact(monkeypatch):
    """GESTION peut préciser un sales_contact_id explicite."""
    _patch_inputs(
        monkeypatch,
        req_values=["Grace Hopper", "grace@example.com", "0600000000", "COBOL Inc."],
        opt_value="7",  # saisi au clavier
        confirm=True,
    )
    service = FakeService()
    auth = AuthContext(user_id=1, role=Role.GESTION)

    created = form_mod.create_client_form(service=service, auth=auth)

    assert service.called is True
    assert created is not None
    assert created.sales_contact_id == 7


def test_create_client_as_gestion_without_sales_contact(monkeypatch):
    """GESTION peut laisser le sales_contact_id vide -> None."""
    _patch_inputs(
        monkeypatch,
        req_values=["Alan Turing", "alan@example.com", "0700000000", "Enigma Ltd"],
        opt_value="",   # vide
        confirm=True,
    )
    service = FakeService()
    auth = AuthContext(user_id=1, role=Role.GESTION)

    created = form_mod.create_client_form(service=service, auth=auth)

    assert service.called is True
    assert created is not None
    assert created.sales_contact_id is None


def test_create_client_cancel_on_confirm(monkeypatch):
    """Si l'utilisateur refuse la confirmation, on annule et on ne call pas le service."""
    _patch_inputs(
        monkeypatch,
        req_values=["X", "x@example.com", "0102030405", "X Corp"],
        confirm=False,  # refuse
    )
    service = FakeService()
    auth = AuthContext(user_id=1, role=Role.GESTION)

    created = form_mod.create_client_form(service=service, auth=auth)

    assert created is None
    assert service.called is False


@pytest.mark.parametrize("cancel_index", [0, 1, 2, 3])
def test_create_client_cancel_during_required_inputs(monkeypatch, cancel_index):
    """
    Annulation à n'importe quelle étape des champs obligatoires (_req_str -> None).
    cancel_index: 0 full_name, 1 email, 2 phone, 3 company_name
    """
    values = ["Ada", "ada@example.com", "0600000000", "Analytical"]
    values[cancel_index] = None  # simulate "retour" -> _req_str returns None

    # Adapter le fake _req_str pour pouvoir renvoyer None
    vals_iter = iter(values)

    def fake_req(_):
        return next(vals_iter)

    def fake_opt(_):  # ne sera pas appelé
        return ""

    def fake_confirm(_):  # ne sera pas appelé
        return True

    monkeypatch.setattr(form_mod, "_req_str", fake_req)
    monkeypatch.setattr(form_mod, "_opt_str", fake_opt)
    monkeypatch.setattr(form_mod, "_confirm", fake_confirm)

    service = FakeService()
    auth = AuthContext(user_id=1, role=Role.GESTION)

    created = form_mod.create_client_form(service=service, auth=auth)

    assert created is None
    assert service.called is False


def test_create_client_authz_error_is_handled(monkeypatch):
    """Si le service lève AuthzError, la fonction capture et retourne None."""
    _patch_inputs(
        monkeypatch,
        req_values=["Bob", "bob@example.com", "0600000000", "BobCorp"],
        opt_value="",
        confirm=True,
    )
    service = FakeService(raise_auth=True)
    auth = AuthContext(user_id=2, role=Role.SUPPORT)  # pas autorisé à créer

    created = form_mod.create_client_form(service=service, auth=auth)

    assert created is None
    assert service.called is True


def test_create_client_gestion_with_invalid_sales_contact_input(monkeypatch):
    """
    GESTION saisit un SC non numérique -> ignoré (reste None) mais création continue.
    """
    _patch_inputs(
        monkeypatch,
        req_values=["Eve", "eve@example.com", "0600000000", "E Corp"],
        opt_value="abc",  # invalide
        confirm=True,
    )
    service = FakeService()
    auth = AuthContext(user_id=1, role=Role.GESTION)

    created = form_mod.create_client_form(service=service, auth=auth)

    assert created is not None
    assert created.sales_contact_id is None