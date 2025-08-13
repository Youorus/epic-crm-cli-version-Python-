import types
import builtins
import pytest

import cli.auth.login as mod


# -------------------------------
# Helpers
# -------------------------------
def _inputs(*answers):
    seq = list(answers)

    def fake_input(prompt=""):
        return seq.pop(0) if seq else ""
    return fake_input


class FakeUser:
    def __init__(self, *, id=1, username="alice", role="Role.GESTION",
                 password_salt=b"x", password_hash=b"y"):
        self.id = id
        self.username = username
        self.role = role
        self.password_salt = password_salt
        self.password_hash = password_hash


# -------------------------------
# login()
# -------------------------------
def test_login_success(monkeypatch, capsys):
    # simulate session_scope context manager (ignored, but must be callable)
    class DummyCM:
        def __enter__(self): return object()
        def __exit__(self, exc_type, exc, tb): return False

    # Fake repo
    class FakeRepo:
        def __init__(self, _): pass
        def get_by_email_or_username(self, ident):
            assert ident == "alice"
            return FakeUser(id=7, username="alice", role="Role.SUPPORT")

    tokens = {}

    monkeypatch.setattr(mod, "session_scope", lambda: DummyCM(), raising=True)
    monkeypatch.setattr(mod, "UserRepo", FakeRepo, raising=True)
    monkeypatch.setattr(mod, "verify_password", lambda pw, s, h: pw == "s3cret", raising=True)
    monkeypatch.setattr(mod, "create_access_token", lambda **kw: "ACCESS", raising=True)
    monkeypatch.setattr(mod, "create_refresh_token", lambda **kw: "REFRESH", raising=True)
    monkeypatch.setattr(mod, "save_tokens", lambda a, r: tokens.update(access=a, refresh=r), raising=True)

    # Inputs
    monkeypatch.setattr(builtins, "input", _inputs("alice"), raising=True)
    monkeypatch.setattr(mod.getpass, "getpass", lambda prompt="": "s3cret", raising=True)

    rc = mod.login()
    out = capsys.readouterr().out

    assert rc == 0
    assert "Connecté en tant que alice" in out
    assert tokens == {"access": "ACCESS", "refresh": "REFRESH"}


def test_login_invalid_ident(monkeypatch, capsys):
    class DummyCM:
        def __enter__(self): return object()
        def __exit__(self, exc_type, exc, tb): return False

    class FakeRepo:
        def __init__(self, _): pass
        def get_by_email_or_username(self, ident):
            return None

    monkeypatch.setattr(mod, "session_scope", lambda: DummyCM(), raising=True)
    monkeypatch.setattr(mod, "UserRepo", FakeRepo, raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("nobody"), raising=True)
    monkeypatch.setattr(mod.getpass, "getpass", lambda prompt="": "x", raising=True)

    rc = mod.login()
    out = capsys.readouterr().out
    assert rc == 1
    assert "Identifiants invalides" in out


def test_login_user_without_password(monkeypatch, capsys):
    class DummyCM:
        def __enter__(self): return object()
        def __exit__(self, exc_type, exc, tb): return False

    class FakeRepo:
        def __init__(self, _): pass
        def get_by_email_or_username(self, ident):
            return FakeUser(password_salt=None, password_hash=None)

    monkeypatch.setattr(mod, "session_scope", lambda: DummyCM(), raising=True)
    monkeypatch.setattr(mod, "UserRepo", FakeRepo, raising=True)
    monkeypatch.setattr(builtins, "input", _inputs("alice"), raising=True)
    monkeypatch.setattr(mod.getpass, "getpass", lambda prompt="": "x", raising=True)

    rc = mod.login()
    out = capsys.readouterr().out
    assert rc == 1
    assert "Utilisateur sans mot de passe défini" in out


def test_login_bad_password(monkeypatch, capsys):
    class DummyCM:
        def __enter__(self): return object()
        def __exit__(self, exc_type, exc, tb): return False

    class FakeRepo:
        def __init__(self, _): pass
        def get_by_email_or_username(self, ident):
            return FakeUser()

    monkeypatch.setattr(mod, "session_scope", lambda: DummyCM(), raising=True)
    monkeypatch.setattr(mod, "UserRepo", FakeRepo, raising=True)
    monkeypatch.setattr(mod, "verify_password", lambda pw, s, h: False, raising=True)

    monkeypatch.setattr(builtins, "input", _inputs("alice"), raising=True)
    monkeypatch.setattr(mod.getpass, "getpass", lambda prompt="": "wrong", raising=True)

    rc = mod.login()
    out = capsys.readouterr().out
    assert rc == 1
    assert "Identifiants invalides" in out


# -------------------------------
# logout()
# -------------------------------
def test_logout(monkeypatch, capsys):
    called = {}

    def fake_clear():
        called["clear"] = True

    monkeypatch.setattr(mod, "clear_token", fake_clear, raising=True)
    rc = mod.logout()
    out = capsys.readouterr().out

    assert rc == 0
    assert called.get("clear") is True
    assert "Déconnecté" in out


# -------------------------------
# whoami()
# -------------------------------
def test_whoami_no_session(monkeypatch, capsys):
    monkeypatch.setattr(mod, "get_auth", lambda: None, raising=True)
    rc = mod.whoami()
    out = capsys.readouterr().out
    assert rc == 1
    assert "Aucune session active" in out


def test_whoami_with_session(monkeypatch, capsys):
    auth = types.SimpleNamespace(user_id=3, role="Role.SUPPORT")
    monkeypatch.setattr(mod, "get_auth", lambda: auth, raising=True)
    rc = mod.whoami()
    out = capsys.readouterr().out
    assert rc == 0
    assert "Session active" in out
    assert "user_id=3" in out
    assert "Role.SUPPORT" in out