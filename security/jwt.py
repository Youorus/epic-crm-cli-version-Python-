# security/jwt.py
from __future__ import annotations
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt  # PyJWT

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-prod-please")
JWT_ALG = "HS256"
ACCESS_EXPIRES_MIN = int(os.getenv("JWT_ACCESS_MIN", "60"))      # ~1h
REFRESH_EXPIRES_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "14"))  # ~2 semaines

@dataclass(frozen=True)
class AuthContext:
    user_id: int
    role: str
    scopes: tuple[str, ...] = ()

class AuthError(Exception): ...

def _now() -> datetime:
    return datetime.now(timezone.utc)

def create_access_token(*, user_id: int, role: str, scopes: Optional[list[str]] = None) -> str:
    now = _now()
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "scopes": scopes or [],
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_EXPIRES_MIN)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def create_refresh_token(*, user_id: int, role: str) -> str:
    now = _now()
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=REFRESH_EXPIRES_DAYS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> AuthContext:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError as e:
        raise AuthError("Token expiré.") from e
    except jwt.InvalidTokenError as e:
        raise AuthError("Token invalide.") from e
    if payload.get("type") != "access":
        raise AuthError("Mauvais type de token (attendu: access).")
    return AuthContext(user_id=int(payload["sub"]), role=str(payload["role"]), scopes=tuple(payload.get("scopes", [])))

def decode_refresh(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError as e:
        raise AuthError("Refresh expiré.") from e
    except jwt.InvalidTokenError as e:
        raise AuthError("Refresh invalide.") from e
    if payload.get("type") != "refresh":
        raise AuthError("Mauvais type de token (attendu: refresh).")
    return payload