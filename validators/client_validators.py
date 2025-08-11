# src/your_app/domain/validators/client_validators.py
from __future__ import annotations
from datetime import date

from validators.validators import (
    ValidationError,
    normalize_email,
    normalize_phone,
    normalize_spaces,
    not_blank,
    max_length,
)

def validate_client_full_name(value: str) -> str:
    v = normalize_spaces(not_blank(value, field="full_name"))
    return max_length(v, field="full_name", max_len=255)

def validate_client_email(value: str) -> str:
    return normalize_email(value, field="email")

def validate_client_phone(value: str) -> str:
    return normalize_phone(value, field="phone", max_len=20)

def validate_company_name(value: str) -> str:
    v = normalize_spaces(not_blank(value, field="company_name"))
    return max_length(v, field="company_name", max_len=255)

def validate_last_contact(value: date | None) -> date | None:
    if value is None:
        return None
    if not isinstance(value, date):
        raise ValidationError("last_contact doit être une date (YYYY-MM-DD).")
    return value