# src/your_app/domain/validators/user_validators.py
from __future__ import annotations
from enums import user_role

from validators.validators  import (
    normalize_email,
    validate_username as _validate_username,
    validate_enum as _validate_enum,
    validate_password as _validate_password,
)

def validate_username(value: str) -> str:
    return _validate_username(value, field="username", max_len=150)

def validate_user_email(value: str) -> str:
    return normalize_email(value, field="email")

def validate_user_role(value: str | user_role, *, enum: type[user_role]) -> user_role:
    return _validate_enum(value, enum=enum, field="role")

def validate_user_password(password: str, *, username: str | None = None, email: str | None = None) -> str:
    forbidden = [u for u in (username, email) if u]
    return _validate_password(password, forbidden_substrings=forbidden)