import types
import pytest

# Module sous test
import cli.services.users.list_users as mod


# ----------------------------
# Fakes / utilitaires
# ----------------------------
class ServiceOK:
    def __init__(self, users):
        self._users = users

    def list(self, *, auth):
        return self._users


class ServiceBoom:
    def list(self, *, auth):
        raise RuntimeError("boom")


def _user(
    *,
    id=1,
    username="alice",
    email="alice@example.com",
    role="GESTION",
    created_at="2025-01-01T12:00:00",
    is_active=True,
):
    # Simple Namespace avec les attributs utilisés par list_users
    return types.SimpleNamespace(
        id=id,
        username=username,
        email=email,
        role=role,
        created_at=created_at,
        is_active=is_active,
    )


# ----------------------------
# Tests
# ----------------------------
def test_permission_denied_returns_empty_and_prints_message(monkeypatch, capsys):
    # can_read_users -> False
    monkeypatch.setattr(mod, "can_read_users", lambda auth: False, raising=True)

    users = mod.list_users(service=ServiceOK([_user()]), auth=object(), display=True, as_table=True)
    captured = capsys.readouterr().out

    assert users == []
    assert "Accès refusé" in captured


def test_empty_list_prints_info_and_returns_empty(monkeypatch, capsys):
    monkeypatch.setattr(mod, "can_read_users", lambda auth: True, raising=True)

    users = mod.list_users(service=ServiceOK([]), auth=object(), display=True, as_table=True)
    out = capsys.readouterr().out

    assert users == []
    assert "Aucun collaborateur" in out



def test_display_plain_prints_lines(monkeypatch, capsys):
    monkeypatch.setattr(mod, "can_read_users", lambda auth: True, raising=True)

    # Pour ce mode, la fonction essaie d'afficher first_name/last_name (non fournis ici).
    # On passe des attributs pour éviter "AttributeError" et vérifier la sortie.
    u = _user(id=3, username="carol", email="carol@example.com", role="COMMERCIAL")
    u.first_name = "Carol"
    u.last_name = "Smith"

    users = mod.list_users(service=ServiceOK([u]), auth=object(), display=True, as_table=False)
    out = capsys.readouterr().out

    assert users == [u]
    assert "- 3: Carol Smith (COMMERCIAL)" in out


def test_no_display_returns_users_but_prints_nothing(monkeypatch, capsys):
    monkeypatch.setattr(mod, "can_read_users", lambda auth: True, raising=True)
    u = _user()

    users = mod.list_users(service=ServiceOK([u]), auth=object(), display=False, as_table=True)
    out = capsys.readouterr().out

    assert users == [u]
    assert out.strip() == ""


def test_service_exception_is_caught_and_returns_empty(monkeypatch, capsys):
    monkeypatch.setattr(mod, "can_read_users", lambda auth: True, raising=True)

    users = mod.list_users(service=ServiceBoom(), auth=object(), display=True, as_table=True)
    out = capsys.readouterr().out

    assert users == []
    assert "Erreur inattendue lors du listing des collaborateurs" in out