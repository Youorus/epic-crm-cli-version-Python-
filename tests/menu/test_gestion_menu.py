import types
import builtins
import pytest

import cli.menu.gestion_menu as mod
from security.authorization import Role


def _auth(role=Role.GESTION, user_id=1):
    return types.SimpleNamespace(role=role, user_id=user_id)


def _inputs(*answers):
    seq = list(answers)
    def fake_input(prompt=""):
        return seq.pop(0) if seq else "0"
    return fake_input


def test_access_denied_if_not_gestion(monkeypatch, capsys):
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(role=Role.COMMERCIAL), raising=True)
    mod.gestion_menu()
    out = capsys.readouterr().out
    assert "réservé au rôle GESTION" in out


def test_option_1_list_clients(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "list_clients", lambda **kw: called.setdefault("list_clients", True), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("1", "0"), raising=True)
    mod.gestion_menu()
    assert called.get("list_clients") is True


def test_option_3_create_contract_form(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "create_contract_form", lambda **kw: called.setdefault("create_contract_form", True), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("3", "0"), raising=True)
    mod.gestion_menu()
    assert called.get("create_contract_form") is True


def test_option_4_update_contract_form(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "update_contract_form", lambda **kw: called.setdefault("update_contract_form", True), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("4", "0"), raising=True)
    mod.gestion_menu()
    assert called.get("update_contract_form") is True


def test_option_5_list_events(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "list_events", lambda **kw: called.setdefault("list_events", []).append(kw), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("5", "0"), raising=True)
    mod.gestion_menu()
    assert called.get("list_events")


def test_option_6_list_events_without_support(monkeypatch):
    calls = []
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "list_events", lambda **kw: calls.append(kw), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("6", "0"), raising=True)
    mod.gestion_menu()
    assert any(k.get("support_isnull") is True for k in calls)


def test_option_7_assign_support(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "assign_support_to_event_form", lambda **kw: called.setdefault("assign", True), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("7", "0"), raising=True)
    mod.gestion_menu()
    assert called.get("assign") is True


def test_option_8_9_10_11_user_actions(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "create_user_form", lambda **kw: called.setdefault("create", True), raising=True)
    monkeypatch.setattr(mod, "update_user_form", lambda **kw: called.setdefault("update", True), raising=True)
    monkeypatch.setattr(mod, "delete_user_form", lambda **kw: called.setdefault("delete", True), raising=True)
    monkeypatch.setattr(mod, "list_users", lambda **kw: called.setdefault("list", True), raising=True)

    # 8 puis 9 puis 10 puis 11 puis 0
    monkeypatch.setattr(builtins, "input", _inputs("8", "9", "10", "11", "0"), raising=True)
    mod.gestion_menu()
    assert called == {"create": True, "update": True, "delete": True, "list": True}


def test_option_12_logout(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "get_auth", lambda: _auth(), raising=True)
    monkeypatch.setattr(mod, "logout", lambda: called.setdefault("logout", True), raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("12"), raising=True)

    mod.gestion_menu()
    assert called.get("logout") is True