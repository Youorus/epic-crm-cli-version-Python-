import types
import pytest
from datetime import datetime, timedelta, timezone

from security.authorization import Role
from cli.services.events import update_event_form as mod


# ------------------------
# Helpers / Doubles
# ------------------------
UTC = timezone.utc
def dt(hours=0):
    return datetime.now(UTC) + timedelta(hours=hours)

class FakeEvent:
    def __init__(self, **kw):
        self.id = kw.get("id", 1)
        self.contract_id = kw.get("contract_id", 10)
        self.client_id = kw.get("client_id", 100)
        self.support_contact_id = kw.get("support_contact_id", 42)
        self.event_name = kw.get("event_name", "Kickoff")
        self.event_start = kw.get("event_start", dt(1))
        self.event_end = kw.get("event_end", dt(2))
        self.location = kw.get("location", "HQ")
        self.attendees = kw.get("attendees", 10)
        self.notes = kw.get("notes", "")

    # Les méthodes du domaine utilisées par le formulaire
    def rename(self, name): self.event_name = name
    def move(self, *, new_start, new_end): self.event_start, self.event_end = new_start, new_end
    def change_location(self, loc): self.location = loc
    def update_notes(self, n): self.notes = n
    def set_attendees(self, n): self.attendees = n

class FakeAuth:
    def __init__(self, user_id=42, role=Role.SUPPORT):
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
def auth_commercial():
    return FakeAuth(user_id=2, role=Role.COMMERCIAL)

@pytest.fixture
def service_ok():
    """Service qui retourne un event et accepte la mise à jour."""
    class S:
        def __init__(self):
            self.updated = None
        def get(self, event_id, *, auth):
            return FakeEvent(id=event_id, support_contact_id=auth.user_id)
        def update(self, event, *, auth):
            self.updated = event
            return event
    return S()

@pytest.fixture(autouse=True)
def patch_parse_dt(monkeypatch):
    """On garde le vrai parseur — mais on peut le monkeypatcher si besoin."""
    # Laisse mod._parse_dt tel quel
    return


# ------------------------
# Tests rôle / early exits
# ------------------------
def test_forbidden_role_returns_none(capsys, auth_commercial, service_ok, monkeypatch):
    # Patch input pour ne jamais être appelé si rôle interdit
    monkeypatch.setattr(mod, "input", lambda prompt="": "should-not-be-used")
    res = mod.update_event_form_support(service=service_ok, auth=auth_commercial)
    assert res is None
    out = capsys.readouterr().out
    assert "Réservé aux rôles SUPPORT / GESTION" in out

def test_cancel_on_retour_at_id(capsys, auth_support, service_ok, monkeypatch):
    inputs = iter(["retour"])
    monkeypatch.setattr(mod, "input", lambda prompt="": next(inputs))
    res = mod.update_event_form_support(service=service_ok, auth=auth_support)
    assert res is None
    out = capsys.readouterr().out
    assert "Annulé." in out

def test_non_digit_id(capsys, auth_support, service_ok, monkeypatch):
    # Saisit "abc", puis "retour"
    inputs = iter(["abc", "retour"])
    monkeypatch.setattr(mod, "input", lambda prompt="": next(inputs))
    res = mod.update_event_form_support(service=service_ok, auth=auth_support)
    assert res is None
    out = capsys.readouterr().out
    assert "L’ID doit être un entier" in out


# ------------------------
# Chargement / erreurs service.get
# ------------------------
def test_event_not_found(capsys, auth_support, monkeypatch):
    class S:
        def get(self, event_id, *, auth): return None
    inputs = iter(["1"])  # id ok → pas de boucle
    monkeypatch.setattr(mod, "input", lambda prompt="": next(inputs))
    res = mod.update_event_form_support(service=S(), auth=auth_support)
    assert res is None
    out = capsys.readouterr().out
    assert "Événement introuvable" in out

def test_authz_error_on_get(capsys, auth_support, monkeypatch):
    class S:
        def get(self, event_id, *, auth):
            from security.authorization import AuthzError
            raise AuthzError("nope")
    inputs = iter(["1"])
    monkeypatch.setattr(mod, "input", lambda prompt="": next(inputs))
    res = mod.update_event_form_support(service=S(), auth=auth_support)
    assert res is None
    out = capsys.readouterr().out
    assert "Accès refusé" in out


# ------------------------
# Saisies invalides
# ------------------------
def test_invalid_dates_format(capsys, auth_support, service_ok, monkeypatch):
    # start et end invalides → _parse_dt doit lever ValueError → le form renvoie None
    bad = "2025-99-99 99:99"
    inputs = iter([
        "1",            # id
        "",             # name (inchangé)
        bad,            # start_raw
        "",             # end_raw (inchangé) → move(new_start, old_end) sera tenté → ValueError
    ])
    # Complète les autres prompts pour éviter StopIteration
    def _fake_input(prompt=""):
        try:
            return next(inputs)
        except StopIteration:
            # champs restants: location, attendees, notes, confirm
            if "lieu" in prompt: return ""
            if "participants" in prompt: return ""
            if "notes" in prompt: return ""
            if "Confirmer" in prompt: return "n"
            return ""

    monkeypatch.setattr(mod, "input", _fake_input)

    # Monkeypatch _parse_dt pour lever ValueError peu importe l’entrée
    monkeypatch.setattr(mod, "_parse_dt", lambda s: (_ for _ in ()).throw(ValueError("format invalide")))
    res = mod.update_event_form_support(service=service_ok, auth=auth_support)
    assert res is None
    out = capsys.readouterr().out
    assert "format invalide" in out

def test_invalid_attendees_non_digit(capsys, auth_support, service_ok, monkeypatch):
    inputs = iter([
        "1",    # id
        "",     # name
        "",     # start
        "",     # end
        "",     # location
        "abc",  # attendees -> invalide
    ])
    def _fake_input(prompt=""):
        try:
            return next(inputs)
        except StopIteration:
            if "notes" in prompt: return ""
            if "Confirmer" in prompt: return "n"
            return ""
    monkeypatch.setattr(mod, "input", _fake_input)

    res = mod.update_event_form_support(service=service_ok, auth=auth_support)
    assert res is None
    out = capsys.readouterr().out
    assert "Participants doit être un entier positif" in out


# ------------------------
# Annulation sur confirmation
# ------------------------
def test_cancel_on_confirm(capsys, auth_support, service_ok, monkeypatch):
    inputs = iter([
        "1",    # id
        "New name",
        "", "",  # start/end inchangés
        "",      # location
        "",      # attendees
        "Some notes",
        "n"      # confirm
    ])
    monkeypatch.setattr(mod, "input", lambda prompt="": next(inputs))
    res = mod.update_event_form_support(service=service_ok, auth=auth_support)
    assert res is None
    out = capsys.readouterr().out
    assert "Annulé" in out


# ------------------------
# Happy path
# ------------------------
def test_happy_path_support_updates_name_time_loc_attendees_notes(capsys, auth_support, service_ok, monkeypatch):
    start = "2025-08-14 10:00"
    end   = "2025-08-14 12:00"
    inputs = iter([
        "1",            # id
        "Kickoff final",# name
        start,          # start
        end,            # end
        "Paris",        # location
        "25",           # attendees
        "Bring beamer", # notes
        "o",            # confirm
    ])
    monkeypatch.setattr(mod, "input", lambda prompt="": next(inputs))
    # On laisse le vrai _parse_dt; il doit accepter le format sans secondes

    res = mod.update_event_form_support(service=service_ok, auth=auth_support)
    # La fonction retourne None par design, mais on vérifie les affichages
    assert res is None

    out = capsys.readouterr().out
    assert "Événement mis à jour" in out
    # Vérifie que le service a bien reçu l'objet modifié
    updated = service_ok.updated
    assert updated is not None
    assert updated.event_name == "Kickoff final"
    assert updated.location == "Paris"
    assert updated.attendees == 25
    assert updated.notes == "Bring beamer"
    # Dates bien parsées et appliquées
    assert updated.event_start.strftime("%Y-%m-%d %H:%M") == "2025-08-14 10:00"
    assert updated.event_end.strftime("%Y-%m-%d %H:%M") == "2025-08-14 12:00"


# ------------------------
# Erreurs update
# ------------------------
def test_authz_error_on_update(capsys, auth_support, monkeypatch):
    class S:
        def get(self, event_id, *, auth): return FakeEvent(id=event_id, support_contact_id=auth.user_id)
        def update(self, event, *, auth):
            from security.authorization import AuthzError
            raise AuthzError("nope")
    # Saisie minimale: id + aucun changement + confirmer
    inputs = iter(["1", "", "", "", "", "", "", "o"])
    monkeypatch.setattr(mod, "input", lambda prompt="": next(inputs))
    res = mod.update_event_form_support(service=S(), auth=auth_support)
    assert res is None
    out = capsys.readouterr().out
    assert "Accès refusé" in out

def test_unexpected_error_on_update(capsys, auth_support, monkeypatch):
    class S:
        def get(self, event_id, *, auth): return FakeEvent(id=event_id, support_contact_id=auth.user_id)
        def update(self, event, *, auth):
            raise RuntimeError("boom")
    inputs = iter(["1", "", "", "", "", "", "", "o"])
    monkeypatch.setattr(mod, "input", lambda prompt="": next(inputs))
    res = mod.update_event_form_support(service=S(), auth=auth_support)
    assert res is None
    out = capsys.readouterr().out
    assert "Erreur lors de l’enregistrement" in out