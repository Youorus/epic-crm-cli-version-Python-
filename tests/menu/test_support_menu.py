import types
import builtins

import cli.menu.support_menu as mod
from security.authorization import Role


def _auth(role=Role.SUPPORT, user_id=7):
    return types.SimpleNamespace(role=role, user_id=user_id)


def _inputs(*answers):
    seq = list(answers)
    def fake_input(prompt=""):
        return seq.pop(0) if seq else "0"
    return fake_input


def test_access_denied_if_not_support_nor_gestion(monkeypatch, capsys):
    monkeypatch.setattr(mod, "get_auth", lambda: types.SimpleNamespace(role=Role.COMMERCIAL, user_id=1), raising=True)
    mod.support_menu()
    out = capsys.readouterr().out
    assert "réservé aux rôles SUPPORT / GESTION" in out


def test_option_1_lists_my_events(monkeypatch):
    calls = []
    def fake_list_events(**kw):
        calls.append(kw)

    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "list_events", fake_list_events, raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("1", "0"), raising=True)

    mod.support_menu()
    assert any(k.get("support_only_mine") is True for k in calls)


def test_option_2_update_event_form_support(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "update_event_form_support", lambda **kw: called.setdefault("update", True), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("2", "0"), raising=True)

    mod.support_menu()
    assert called.get("update") is True


def test_option_3_logout(monkeypatch, capsys):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "logout", lambda: called.setdefault("logout", True), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("3"), raising=True)

    mod.support_menu()
    assert called.get("logout") is True
    out = capsys.readouterr().out
    assert "Déconnecté" in out