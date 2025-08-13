import types
import builtins
import pytest

import cli.menu.commercial_menu as mod
from security.authorization import Role


def _auth(role=Role.COMMERCIAL, user_id=42):
    return types.SimpleNamespace(role=role, user_id=user_id)


def _inputs(*answers):
    seq = list(answers)
    def fake_input(prompt=""):
        return seq.pop(0) if seq else "0"  # default: retour
    return fake_input


def test_access_denied_if_not_commercial(monkeypatch, capsys):
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(role=Role.GESTION), raising=True)
    mod.commercial_menu()
    out = capsys.readouterr().out
    assert "réservé au rôle COMMERCIAL" in out


def test_access_denied_if_not_logged(monkeypatch, capsys):
    monkeypatch.setattr(mod, "get_auth", lambda: None, raising=True)
    mod.commercial_menu()
    out = capsys.readouterr().out
    assert "Session expirée" in out


def test_option_1_lists_clients(monkeypatch, capsys):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "list_clients", lambda **kw: called.setdefault("list_clients", True), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("1", "0"), raising=True)

    mod.commercial_menu()
    assert called.get("list_clients") is True


def test_option_2_create_client_form(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "create_client_form", lambda **kw: called.setdefault("create_client_form", True), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("2", "0"), raising=True)

    mod.commercial_menu()
    assert called.get("create_client_form") is True


def test_option_3_update_client_form(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "update_client_form", lambda **kw: called.setdefault("update_client_form", True), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("3", "0"), raising=True)

    mod.commercial_menu()
    assert called.get("update_client_form") is True


def test_option_4_list_contracts(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "list_contracts", lambda **kw: called.setdefault("list_contracts", []).append(kw), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("4", "0"), raising=True)

    mod.commercial_menu()
    assert called.get("list_contracts")


def test_option_5_list_contracts_unsigned(monkeypatch):
    calls = []
    def fake_list_contracts(**kw):
        calls.append(kw)
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "list_contracts", fake_list_contracts, raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("5", "0"), raising=True)

    mod.commercial_menu()
    assert any(k.get("filter_signed") is False for k in calls)


def test_option_6_list_contracts_min_due(monkeypatch):
    calls = []
    def fake_list_contracts(**kw):
        calls.append(kw)
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "list_contracts", fake_list_contracts, raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("6", "0"), raising=True)

    mod.commercial_menu()
    assert any(k.get("min_due") == 0.01 for k in calls)


def test_option_7_create_event_form(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "create_event_form", lambda **kw: called.setdefault("create_event_form", True), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("7", "0"), raising=True)

    mod.commercial_menu()
    assert called.get("create_event_form") is True


def test_option_9_logout(monkeypatch, capsys):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "logout", lambda: called.setdefault("logout", True), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("9"), raising=True)

    mod.commercial_menu()
    assert called.get("logout") is True
    out = capsys.readouterr().out
    assert "Déconnecté" in out