# security/session_state.py
from __future__ import annotations
import json, os
from typing import Optional
from security.jwt import decode_token, decode_refresh, create_access_token, AuthContext, AuthError

_SESSION_DIR = os.path.join(os.path.expanduser("~"), ".epic_events")
_SESSION_FILE = os.path.join(_SESSION_DIR, "session.json")

_current_access: Optional[str] = None
_current_refresh: Optional[str] = None
_current_auth: Optional[AuthContext] = None

def save_tokens(access_token: str, refresh_token: str) -> None:
    """Enregistre les deux tokens (mémoire + fichier)."""
    global _current_access, _current_refresh, _current_auth
    os.makedirs(_SESSION_DIR, exist_ok=True)
    with open(_SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump({"access": access_token, "refresh": refresh_token}, f)
    _current_access = access_token
    _current_refresh = refresh_token
    _current_auth = decode_token(access_token)

def load_tokens() -> tuple[Optional[str], Optional[str]]:
    global _current_access, _current_refresh, _current_auth
    if _current_access and _current_refresh:
        return _current_access, _current_refresh
    if not os.path.exists(_SESSION_FILE):
        return None, None
    try:
        with open(_SESSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        _current_access = data.get("access")
        _current_refresh = data.get("refresh")
        if _current_access:
            try:
                _current_auth = decode_token(_current_access)
            except Exception:
                _current_auth = None
        return _current_access, _current_refresh
    except Exception:
        return None, None

def clear_token() -> None:
    global _current_access, _current_refresh, _current_auth
    _current_access = None
    _current_refresh = None
    _current_auth = None
    try:
        if os.path.exists(_SESSION_FILE):
            os.remove(_SESSION_FILE)
    except Exception:
        pass

def ensure_access_token() -> Optional[str]:
    """
    Renvoie un access token valide.
    - Si l'access en mémoire/fichier est valide → renvoie tel quel.
    - S'il est expiré mais que le refresh est valide → régénère un access, sauve et renvoie.
    - Sinon → None (il faudra se reconnecter).
    """
    global _current_access, _current_refresh, _current_auth
    access, refresh = load_tokens()

    if access:
        try:
            _current_auth = decode_token(access)
            _current_access = access
            return access
        except AuthError:
            # expiré/invalide → on tentera le refresh
            pass

    if not refresh:
        return None

    # Tenter refresh → re-créer un access à partir des claims refresh
    try:
        payload = decode_refresh(refresh)
    except AuthError:
        clear_token()
        return None

    new_access = create_access_token(user_id=int(payload["sub"]), role=str(payload["role"]))
    save_tokens(new_access, refresh)
    return new_access

def get_auth() -> Optional[AuthContext]:
    """Renvoie l'AuthContext courant (après refresh auto si nécessaire)."""
    global _current_auth
    token = ensure_access_token()
    if not token:
        return None
    # ensure_access_token a déjà peuplé _current_auth si possible
    if _current_auth:
        return _current_auth
    try:
        _current_auth = decode_token(token)
        return _current_auth
    except Exception:
        clear_token()
        return None