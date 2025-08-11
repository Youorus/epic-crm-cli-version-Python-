# src/your_app/domain/validators/shared_validators.py
from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from enums import user_role
from typing import Optional, Iterable, Any

# ——————————————————————————————
# Erreur commune
# ——————————————————————————————
class ValidationError(ValueError):
    pass

# ——————————————————————————————
# Chaînes / formats
# ——————————————————————————————
_WHITESPACE_RE = re.compile(r"\s+")

def normalize_spaces(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", (value or "").strip())

def not_blank(value: str, *, field: str) -> str:
    v = (value or "").strip()
    if not v:
        raise ValidationError(f"{field} ne peut pas être vide.")
    return v

def max_length(value: str, *, field: str, max_len: int) -> str:
    if len(value) > max_len:
        raise ValidationError(f"{field} dépasse {max_len} caractères.")
    return value

# ——————————————————————————————
# Email / téléphone
# ——————————————————————————————
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def normalize_email(value: str, *, field: str = "email") -> str:
    v = normalize_spaces(not_blank(value, field=field)).lower()
    if not _EMAIL_RE.match(v):
        raise ValidationError(f"{field} invalide.")
    return v

_PHONE_CLEAN_RE = re.compile(r"[^\d+]")
def normalize_phone(value: str, *, field: str = "phone", max_len: int = 20) -> str:
    v = not_blank(value, field=field)
    v = _PHONE_CLEAN_RE.sub("", v)
    if not v or v.count("+") > 1 or (v.startswith("+") and len(v) == 1):
        raise ValidationError(f"{field} invalide.")
    if len(v) > max_len:
        raise ValidationError(f"{field} dépasse {max_len} caractères.")
    return v

# ——————————————————————————————
# Enums / username / password
# ——————————————————————————————
def validate_enum(value: Any, *, enum: type[user_role], field: str = "value") -> user_role:
    if isinstance(value, enum):
        return value
    sval = str(value).strip()
    for m in enum:
        if m.name == sval.upper() or (isinstance(m.value, str) and m.value.upper() == sval.upper()):
            return m
    allowed = ", ".join(m.name for m in enum)
    raise ValidationError(f"{field} inconnu. Valeurs autorisées: {allowed}.")

def validate_username(value: str, *, field: str = "username", max_len: int = 150) -> str:
    v = normalize_spaces(not_blank(value, field=field))
    v = max_length(v, field=field, max_len=max_len)
    if not re.match(r"^[\w.@+-]+$", v):
        raise ValidationError(f"{field} contient des caractères non autorisés.")
    return v

_DEFAULT_COMMON = frozenset({"password", "12345678", "qwertyui", "azertyui", "admin", "welcome", "letmein"})
def validate_password(
    value: str,
    *,
    field: str = "password",
    min_len: int = 8,
    require_upper: bool = True,
    require_lower: bool = True,
    require_digit: bool = True,
    require_special: bool = True,
    forbidden_substrings: Iterable[str] = (),
    disallow_common: bool = True,
    common_set: Iterable[str] = _DEFAULT_COMMON,
) -> str:
    v = value or ""
    if len(v) < min_len:
        raise ValidationError(f"{field} doit contenir au moins {min_len} caractères.")
    if require_upper and not re.search(r"[A-Z]", v):
        raise ValidationError(f"{field} doit contenir au moins une majuscule.")
    if require_lower and not re.search(r"[a-z]", v):
        raise ValidationError(f"{field} doit contenir au moins une minuscule.")
    if require_digit and not re.search(r"\d", v):
        raise ValidationError(f"{field} doit contenir au moins un chiffre.")
    if require_special and not re.search(r"[^\w\s]", v):
        raise ValidationError(f"{field} doit contenir au moins un caractère spécial.")
    if disallow_common and v.lower() in {c.lower() for c in common_set}:
        raise ValidationError(f"{field} est trop commun.")
    for s in forbidden_substrings:
        if s and s.lower() in v.lower():
            raise ValidationError(f"{field} ne doit pas contenir: « {s} ».")
    return v

# ——————————————————————————————
# Montants (Decimal)
# ——————————————————————————————
from decimal import Decimal

def q2(value: Decimal | int | float | str, *, field: str = "amount") -> Decimal:
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"{field} invalide.") from exc
    try:
        return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception as exc:
        raise ValidationError(f"{field} invalide.") from exc

def money_in_range(
    value: Decimal | int | float | str,
    *,
    field: str,
    min_: Optional[Decimal | int | float | str] = None,
    max_: Optional[Decimal | int | float | str] = None,
) -> Decimal:
    d = q2(value, field=field)
    if min_ is not None and d < q2(min_, field=field):
        raise ValidationError(f"{field} doit être ≥ {q2(min_, field=field)}.")
    if max_ is not None and d > q2(max_, field=field):
        raise ValidationError(f"{field} doit être ≤ {q2(max_, field=field)}.")
    return d

def validate_due_vs_total(amount_due: Decimal, total_amount: Decimal, *, field_due="amount_due", field_total="total_amount") -> None:
    if amount_due < Decimal("0.00"):
        raise ValidationError(f"{field_due} doit être ≥ 0.")
    if total_amount < Decimal("0.00"):
        raise ValidationError(f"{field_total} doit être ≥ 0.")
    if amount_due > total_amount:
        raise ValidationError(f"{field_due} ne peut pas dépasser {field_total}.")

# ——————————————————————————————
# Nombres entiers / dates
# ——————————————————————————————
def positive_int(value: Any, *, field: str = "value", min_: int = 1, max_: Optional[int] = None) -> int:
    try:
        n = int(value)
    except Exception as exc:
        raise ValidationError(f"{field} doit être un entier.") from exc
    if n < min_:
        raise ValidationError(f"{field} doit être ≥ {min_}.")
    if max_ is not None and n > max_:
        raise ValidationError(f"{field} doit être ≤ {max_}.")
    return n

def ensure_aware_utc(dt: datetime, *, field: str) -> datetime:
    if not isinstance(dt, datetime):
        raise ValidationError(f"{field} doit être un datetime.")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def ensure_order(start: datetime, end: datetime, *, field_start: str, field_end: str) -> None:
    if end < start:
        raise ValidationError(f"{field_end} doit être ≥ {field_start}.")