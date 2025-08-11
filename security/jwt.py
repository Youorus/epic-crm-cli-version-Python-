# security/jwt.py
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

# Idéalement via variables d'env
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-prod-please")
JWT_ALG = "HS256"
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "60"))


@dataclass(frozen=True)
class AuthContext:
    user_id: int
    role: str
    scopes: tuple[str, ...] = ()

    def has_role(self, *roles: str) -> bool:
        r = self.role.upper()
        return any(r == rr.upper() for rr in roles)

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes


class AuthError(Exception):
    pass


def create_access_token(*, user_id: int, role: str, scopes: Optional[list[str]] = None, expires_minutes: int = JWT_EXPIRES_MIN) -> str:
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "scopes": scopes or [],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> AuthContext:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError as e:
        raise AuthError("Token expiré.") from e
    except jwt.InvalidTokenError as e:
        raise AuthError("Token invalide.") from e

    try:
        user_id = int(payload["sub"])
        role = str(payload["role"])
        scopes = tuple(payload.get("scopes", []))
    except Exception as e:
        raise AuthError("Payload de token invalide.") from e

    return AuthContext(user_id=user_id, role=role, scopes=scopes)