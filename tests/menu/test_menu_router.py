import types
import cli.menu.menu_router as mod


def test_router_calls_gestion_menu(monkeypatch, capsys):
    called = {}
    monkeypatch.setattr(mod, "gestion_menu", lambda: called.setdefault("gestion", True), raising=True)
    monkeypatch.setattr(mod, "commercial_menu", lambda: called.setdefault("commercial", True), raising=True)
    monkeypatch.setattr(mod, "support_menu", lambda: called.setdefault("support", True), raising=True)

    monkeypatch.setattr(mod, "_current_role", lambda: "GESTION", raising=True)
    monkeypatch.setattr(mod, "_current_username", lambda: "alice", raising=True)

    mod.show_menu()
    assert called == {"gestion": True}


def test_router_calls_commercial_menu(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "gestion_menu", lambda: called.setdefault("gestion", True), raising=True)
    monkeypatch.setattr(mod, "commercial_menu", lambda: called.setdefault("commercial", True), raising=True)
    monkeypatch.setattr(mod, "support_menu", lambda: called.setdefault("support", True), raising=True)

    monkeypatch.setattr(mod, "_current_role", lambda: "COMMERCIAL", raising=True)
    monkeypatch.setattr(mod, "_current_username", lambda: "bob", raising=True)

    mod.show_menu()
    assert called == {"commercial": True}


def test_router_calls_support_menu(monkeypatch):
    called = {}
    monkeypatch.setattr(mod, "gestion_menu", lambda: called.setdefault("gestion", True), raising=True)
    monkeypatch.setattr(mod, "commercial_menu", lambda: called.setdefault("commercial", True), raising=True)
    monkeypatch.setattr(mod, "support_menu", lambda: called.setdefault("support", True), raising=True)

    monkeypatch.setattr(mod, "_current_role", lambda: "SUPPORT", raising=True)
    monkeypatch.setattr(mod, "_current_username", lambda: "carol", raising=True)

    mod.show_menu()
    assert called == {"support": True}


def test_router_when_no_role(monkeypatch, capsys):
    monkeypatch.setattr(mod, "_current_role", lambda: None, raising=True)
    monkeypatch.setattr(mod, "_current_username", lambda: None, raising=True)

    mod.show_menu()
    out = capsys.readouterr().out
    assert "Aucun utilisateur connecté" in out


def test_router_unknown_role(monkeypatch, capsys):
    monkeypatch.setattr(mod, "_current_role", lambda: "UNKNOWN", raising=True)
    monkeypatch.setattr(mod, "_current_username", lambda: "zoe", raising=True)

    mod.show_menu()
    out = capsys.readouterr().out
    assert "Rôle non reconnu" in out