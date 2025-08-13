# tests/security/test_auth_session.py
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

import pytest

import security.auth_session as auth_session
from security.authorization import Role


# ─────────────────────────────────────────────────────────
# Fixtures utilitaires
# ─────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def tmp_session_dir(monkeypatch, tmp_path):
    """
    Redirige le fichier de session vers un répertoire temporaire
    pour ne jamais toucher le home de l'utilisateur.
    Réinitialise les "globals" entre les tests.
    """
    session_dir = tmp_path / ".epic_events"
    session_dir.mkdir()
    monkeypatch.setattr(auth_session, "_SESSION_DIR", str(session_dir))
    monkeypatch.setattr(auth_session, "_SESSION_FILE", str(session_dir / "session.json"))

    # Reset des variables globales du module
    auth_session._current_access = None
    auth_session._current_refresh = None
    auth_session._current_auth = None

    yield


@pytest.fixture
def fake_auth_types(monkeypatch):
    """
    Remplace AuthContext / AuthError importés par auth_session
    par des implémentations minimales contrôlables par le test.
    """
    @dataclass(frozen=True)
    class DummyAuthContext:
        user_id: int
        role: Any  # str ou Role

    class DummyAuthError(Exception):
        pass

    monkeypatch.setattr(auth_session, "AuthContext", DummyAuthContext, raising=False)
    monkeypatch.setattr(auth_session, "AuthError", DummyAuthError, raising=False)

    return DummyAuthContext, DummyAuthError


# ─────────────────────────────────────────────────────────
# Helpers de monkeypatch decode/encode
# ─────────────────────────────────────────────────────────

def _patch_decode_token(monkeypatch, ret):
    """ret peut être un objet à retourner, ou une exception à lever."""
    def _decode_token(_token):
        if isinstance(ret, Exception):
            raise ret
        return ret
    monkeypatch.setattr(auth_session, "decode_token", _decode_token, raising=True)


def _patch_decode_refresh(monkeypatch, payload: Dict[str, Any] | Exception):
    def _decode_refresh(_token):
        if isinstance(payload, Exception):
            raise payload
        return payload
    monkeypatch.setattr(auth_session, "decode_refresh", _decode_refresh, raising=True)


def _patch_create_access_token(monkeypatch, value: str):
    monkeypatch.setattr(auth_session, "create_access_token", lambda **kw: value, raising=True)


# ─────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────

def test_save_and_load_tokens_normalizes_role(monkeypatch, fake_auth_types, tmp_path):
    DummyAuthContext, _ = fake_auth_types

    # decode_token renvoie un AuthContext avec role en STR
    _patch_decode_token(monkeypatch, DummyAuthContext(user_id=42, role="GESTION"))

    # Sauvegarde
    auth_session.save_tokens("access-aaa", "refresh-rrr")

    # Le fichier a bien été créé
    with open(auth_session._SESSION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["access"] == "access-aaa"
    assert data["refresh"] == "refresh-rrr"

    # L'auth courante est normalisée → Role enum
    assert auth_session._current_auth is not None
    assert auth_session._current_auth.role is Role.GESTION

    # On réinitialise en mémoire et on relit depuis le disque
    auth_session._current_access = None
    auth_session._current_refresh = None
    auth_session._current_auth = None

    acc, ref = auth_session.load_tokens()
    assert acc == "access-aaa"
    assert ref == "refresh-rrr"
    # decode_token a été rejoué → normalisation OK
    assert auth_session._current_auth is not None
    assert auth_session._current_auth.role is Role.GESTION


def test_ensure_access_token_valid(monkeypatch, fake_auth_types):
    DummyAuthContext, DummyAuthError = fake_auth_types
    # Token valide → decode_token renvoie un contexte directement
    _patch_decode_token(monkeypatch, DummyAuthContext(user_id=1, role=Role.SUPPORT))

    auth_session.save_tokens("acc-valid", "ref-xxx")
    token = auth_session.ensure_access_token()
    assert token == "acc-valid"
    assert auth_session._current_auth is not None
    assert auth_session._current_auth.role is Role.SUPPORT



def test_clear_token_removes_file_and_globals(monkeypatch, fake_auth_types):
    DummyAuthContext, _ = fake_auth_types
    _patch_decode_token(monkeypatch, DummyAuthContext(user_id=1, role="GESTION"))

    auth_session.save_tokens("acc", "ref")
    # Sanity
    assert auth_session._current_access == "acc"
    assert auth_session._current_refresh == "ref"
    assert auth_session._current_auth is not None

    auth_session.clear_token()

    assert auth_session._current_access is None
    assert auth_session._current_refresh is None
    assert auth_session._current_auth is None

    # Le fichier a été supprimé (ou au moins, inexistant après clear)
    assert not (auth_session._SESSION_FILE and
                __import__("os").path.exists(auth_session._SESSION_FILE))