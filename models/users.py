from __future__ import annotations

import os, hmac, hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from enums.user_role import UserRole

# User field validators
from validators.user_validators import (
    validate_username,
    normalize_email,
)
from validators.validators import validate_password, validate_enum


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)



# scrypt (exemple pédagogique) — préfère argon2/bcrypt en prod
SCRYPT_N, SCRYPT_R, SCRYPT_P, SCRYPT_LEN, SCRYPT_SALT_LEN = 2**14, 8, 1, 64, 16

def _hash_password(plain: str, *, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    if not plain:
        raise ValueError("Le mot de passe ne peut pas être vide.")
    salt = salt or os.urandom(SCRYPT_SALT_LEN)
    digest = hashlib.scrypt(plain.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=SCRYPT_LEN)
    return salt, digest

def _ct_eq(a: bytes, b: bytes) -> bool:
    return hmac.compare_digest(a, b)

@dataclass(slots=True)
class User:
    # Identité
    username: str
    email: str
    role: UserRole

    # États/permissions
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False

    # Audit / auth
    last_login: Optional[datetime] = None
    date_joined: datetime = field(default_factory=_utcnow)

    # Techniques
    id: Optional[int] = None
    created_at: datetime = field(default_factory=_utcnow, kw_only=True)
    updated_at: datetime = field(default_factory=_utcnow, kw_only=True)

    _password_salt: Optional[bytes] = field(default=None, repr=False)
    _password_hash: Optional[bytes] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.username = validate_username(self.username)
        self.email = normalize_email(self.email)
        self.role = validate_enum(self.role, enum=UserRole, field="role")  # accepte str/Enum

    def touch(self) -> None:
        self.updated_at = _utcnow()

    # Mot de passe
    def set_password(self, plain: str) -> None:
        # politique configurable ; évite nom/email
        validate_password(plain, forbidden_substrings=[self.username, self.email])
        salt, digest = _hash_password(plain)
        self._password_salt, self._password_hash = salt, digest
        self.touch()

    def check_password(self, plain: str) -> bool:
        if not (self._password_salt and self._password_hash):
            return False
        _, digest = _hash_password(plain, salt=self._password_salt)
        return _ct_eq(digest, self._password_hash)

    def clear_password(self) -> None:
        self._password_salt = self._password_hash = None
        self.touch()

    # Rôles & états
    def set_role(self, role: UserRole | str) -> None:
        self.role = validate_enum(role, enum=UserRole, field="role")
        self.touch()

    def mark_login(self, when: Optional[datetime] = None) -> None:
        self.last_login = (when or _utcnow()).astimezone(timezone.utc)
        self.touch()


    # Sérialisation
    def to_dict(self, *, include_private: bool = False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_staff": self.is_staff,
            "is_superuser": self.is_superuser,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "date_joined": self.date_joined.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_private:
            data["_password_salt"] = self._password_salt.hex() if self._password_salt else None
            data["_password_hash"] = self._password_hash.hex() if self._password_hash else None
        return data

    # Factory
    @classmethod
    def create(
        cls,
        *,
        username: str,
        email: str,
        role: UserRole | str,
        password: Optional[str] = None,
        is_active: bool = True,
        is_staff: bool = False,
        is_superuser: bool = False,
    ) -> "User":
        u = cls(username=username, email=email, role=role, is_active=is_active, is_staff=is_staff, is_superuser=is_superuser)
        if password:
            u.set_password(password)
        return u

    def __str__(self) -> str:
        return f"{self.username} ({self.role.value})"