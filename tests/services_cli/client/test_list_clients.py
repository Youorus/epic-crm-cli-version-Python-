# tests/cli/services/clients/test_list_clients.py
from __future__ import annotations

import re
from datetime import datetime, date, timezone

import pytest

from security.authorization import AuthContext, Role, AuthzError
from models.clients import Client

# Module sous test
import cli.services.clients.list_clients as mod


class FakeService:
    def __init__(self, items=None, raise_auth=False):
        self.items = list(items or [])
        self.raise_auth = raise_auth
        self.called = False

    def list(self, *, auth: AuthContext):
        self.called = True
        if self.raise_auth:
            raise AuthzError("forbidden")
        return self.items


def _client(
    *,
    cid: int,
    full_name: str = "John Doe",
    company_name: str = "Acme Corp",
    email: str = "john@example.com",
    phone: str = "0600000000",
    sales_contact_id: int | None = None,
    last_contact: date | None = None,
    created_at: datetime | None = None,
):
    # Datetimes “propres” pour l’affichage
    created_at = created_at or datetime(2025, 1, 2, 10, 30, tzinfo=timezone.utc)
    return Client(
        id=cid,
        full_name=full_name,
        email=email,
        phone=phone,
        company_name=company_name,
        last_contact=last_contact,
        sales_contact_id=sales_contact_id,
        created_at=created_at,
        updated_at=created_at,
    )


def test_list_clients_table_happy_path(monkeypatch, capsys):
    """Affichage tableau avec résolution des noms de commerciaux."""
    c1 = _client(cid=1, full_name="Ada Lovelace", company_name="Analytical", sales_contact_id=2,
                 last_contact=date(2025, 1, 1))
    c2 = _client(cid=2, full_name="Alan Turing", company_name="Enigma", sales_contact_id=None)

    service = FakeService(items=[c1, c2])
    auth = AuthContext(user_id=1, role=Role.GESTION)

    # On force la map id->nom du commercial
    monkeypatch.setattr(mod, "_load_sales_contact_names", lambda: {2: "commercial"})

    items = mod.list_clients(
        service=service,
        auth=auth,
        search=None,
        display=True,
        as_table=True,
    )

    out = capsys.readouterr().out

    # entête + contenu de base
    assert "=== LISTE DES CLIENTS ===" in out
    assert "Ada Lovelace" in out
    assert "Alan Turing" in out
    # nom résolu pour sales_contact_id=2
    assert "commercial" in out
    # pour None -> tiret
    assert re.search(r"\s—\s", out) or "—" in out

    assert service.called is True
    assert items == [c1, c2]


def test_list_clients_search_filters(monkeypatch, capsys):
    """Le filtre `search` restreint le résultat côté CLI."""
    c1 = _client(cid=1, full_name="Ada Lovelace", company_name="Analytical")
    c2 = _client(cid=2, full_name="Alan Turing", company_name="Enigma")
    service = FakeService(items=[c1, c2])
    auth = AuthContext(user_id=2, role=Role.COMMERCIAL)

    # pas d'accès à la DB user dans ce test
    monkeypatch.setattr(mod, "_load_sales_contact_names", lambda: {})

    items = mod.list_clients(
        service=service,
        auth=auth,
        search="enigma",   # doit ne garder que Alan
        display=True,
        as_table=True,
    )

    out = capsys.readouterr().out
    assert "Ada Lovelace" not in out
    assert "Alan Turing" in out
    assert items == [c2]


def test_list_clients_no_items_prints_message(monkeypatch, capsys):
    """Quand la liste est vide, un message est affiché et [] est renvoyé."""
    service = FakeService(items=[])
    auth = AuthContext(user_id=1, role=Role.GESTION)

    monkeypatch.setattr(mod, "_load_sales_contact_names", lambda: {})

    items = mod.list_clients(
        service=service,
        auth=auth,
        search=None,
        display=True,
        as_table=True,
    )

    out = capsys.readouterr().out
    assert "Aucun client trouvé" in out
    assert items == []


def test_list_clients_display_false_returns_without_print(monkeypatch, capsys):
    """display=False retourne la liste sans rien imprimer."""
    c1 = _client(cid=1)
    c2 = _client(cid=2)
    service = FakeService(items=[c1, c2])
    auth = AuthContext(user_id=3, role=Role.SUPPORT)

    monkeypatch.setattr(mod, "_load_sales_contact_names", lambda: {"x": "y"})

    items = mod.list_clients(
        service=service,
        auth=auth,
        search=None,
        display=False,   # <-- pas d'affichage
        as_table=True,
    )

    out = capsys.readouterr().out
    assert out == ""  # rien imprimé
    assert items == [c1, c2]


def test_list_clients_authz_error(monkeypatch, capsys):
    """Si le service lève AuthzError, on affiche un message et on renvoie []."""
    service = FakeService(raise_auth=True)
    auth = AuthContext(user_id=99, role=Role.SUPPORT)

    items = mod.list_clients(
        service=service,
        auth=auth,
        search=None,
        display=True,
        as_table=True,
    )

    out = capsys.readouterr().out
    assert "Accès refusé" in out
    assert items == []


def test_list_clients_fallback_when_user_mapping_crashes(monkeypatch, capsys):
    """Si _load_sales_contact_names() plante, on retombe sur un affichage sans noms résolus."""
    c = _client(cid=1, full_name="Eve", company_name="E Corp", sales_contact_id=123)
    service = FakeService(items=[c])
    auth = AuthContext(user_id=1, role=Role.GESTION)

    def boom():
        raise RuntimeError("DB down")

    monkeypatch.setattr(mod, "_load_sales_contact_names", boom)

    items = mod.list_clients(service=service, auth=auth, display=True, as_table=True)

    out = capsys.readouterr().out
    # pas de crash, le client est affiché
    assert "Eve" in out
    # quand on ne peut pas résoudre, on affiche un tiret ou un fallback
    assert "—" in out or "User #123" in out
    assert items == [c]