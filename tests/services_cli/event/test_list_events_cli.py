import types
import pytest
from datetime import datetime, timedelta, timezone

from security.authorization import AuthzError, Role
from cli.services.events import list_events as list_mod


# ------------------------
# Helpers / Doubles
# ------------------------
UTC = timezone.utc
def dt(hours=0):
    return datetime.now(UTC) + timedelta(hours=hours)

class FakeEvent:
    def __init__(self, **kw):
        self.id = kw.get("id")
        self.client_id = kw.get("client_id")
        self.support_contact_id = kw.get("support_contact_id")
        self.event_name = kw.get("event_name", "Dummy")
        self.event_start = kw.get("event_start", dt(1))
        self.event_end = kw.get("event_end", dt(2))
        self.location = kw.get("location", "Somewhere")
        self.attendees = kw.get("attendees", 10)
        self.notes = kw.get("notes", "")
        self.created_at = kw.get("created_at", dt(0))

class FakeAuth:
    def __init__(self, user_id=7, role=Role.SUPPORT):
        self.user_id = user_id
        self.role = role


# ------------------------
# Fixtures
# ------------------------
@pytest.fixture
def auth_support():
    return FakeAuth(user_id=42, role=Role.SUPPORT)

@pytest.fixture
def auth_gestion():
    return FakeAuth(user_id=1, role=Role.GESTION)

@pytest.fixture
def events_sample():
    # 3 événements : un sans support, deux avec support (42 et 99)
    return [
        FakeEvent(id=1, client_id=10, support_contact_id=None, event_name="A"),
        FakeEvent(id=2, client_id=11, support_contact_id=42,   event_name="B"),
        FakeEvent(id=3, client_id=12, support_contact_id=99,   event_name="C"),
    ]

@pytest.fixture
def service_mock(events_sample):
    class _S:
        def list(self, *, auth):
            return events_sample
    return _S()

@pytest.fixture(autouse=True)
def patch_build_maps(monkeypatch):
    # Empêche toute requête DB pour récupérer noms clients/users
    monkeypatch.setattr(list_mod, "_build_maps", lambda _events: ({}, {}))
    return


# ------------------------
# Tests happy path
# ------------------------

def test_list_events_detail_display(service_mock, auth_gestion, capsys):
    items = list_mod.list_events(service=service_mock, auth=auth_gestion, display=True, as_table=False)
    assert len(items) == 3
    out = capsys.readouterr().out
    assert "LISTE DES ÉVÉNEMENTS (détails)" in out
    assert "🆔 ID" in out

def test_list_events_no_display_returns_items(service_mock, auth_gestion, capsys):
    items = list_mod.list_events(service=service_mock, auth=auth_gestion, display=False, as_table=True)
    # Pas d’affichage, mais items renvoyés
    assert len(items) == 3
    out = capsys.readouterr().out
    assert out == ""


# ------------------------
# Filtres
# ------------------------
def test_filter_support_isnull_true(service_mock, auth_gestion, capsys):
    items = list_mod.list_events(service=service_mock, auth=auth_gestion, support_isnull=True)
    # Garde uniquement ceux sans support → ID=1
    assert [e.id for e in items] == [1]

def test_filter_support_isnull_false(service_mock, auth_gestion, capsys):
    items = list_mod.list_events(service=service_mock, auth=auth_gestion, support_isnull=False)
    # Garde ceux avec support → 2 et 3
    assert sorted(e.id for e in items) == [2, 3]

def test_filter_support_only_mine(service_mock, auth_support, capsys):
    # auth_support.user_id == 42 → ne garde que support_contact_id = 42
    items = list_mod.list_events(service=service_mock, auth=auth_support, support_only_mine=True)
    assert [e.id for e in items] == [2]

def test_filter_support_contact_id_explicit(service_mock, auth_gestion, capsys):
    # Filtre explicite par support 99 → ID=3
    items = list_mod.list_events(service=service_mock, auth=auth_gestion, support_contact_id=99)
    assert [e.id for e in items] == [3]


# ------------------------
# Aucun résultat
# ------------------------
def test_no_items_after_filters_prints_message(service_mock, auth_gestion, capsys):
    items = list_mod.list_events(
        service=service_mock, auth=auth_gestion, support_isnull=False, support_contact_id=12345
    )
    assert items == []
    out = capsys.readouterr().out
    assert "Aucun événement trouvé" in out


# ------------------------
# Erreurs
# ------------------------
def test_authz_error_is_caught(capsys, monkeypatch, auth_gestion):
    class _S:
        def list(self, *, auth):
            raise AuthzError("nope")
    items = list_mod.list_events(service=_S(), auth=auth_gestion)
    assert items == []
    out = capsys.readouterr().out
    assert "Accès refusé" in out

def test_unexpected_error_is_caught(capsys, monkeypatch, auth_gestion):
    class _S:
        def list(self, *, auth):
            raise RuntimeError("boom")
    items = list_mod.list_events(service=_S(), auth=auth_gestion)
    assert items == []
    out = capsys.readouterr().out
    assert "Erreur inattendue lors du listing des événements" in out