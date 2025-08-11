# src/your_app/domain/validators/event_validators.py
from __future__ import annotations
from datetime import datetime

from validators.validators  import (
    ValidationError,
    not_blank,
    max_length,
    positive_int,
    ensure_aware_utc,
    ensure_order,
)

def validate_event_name(value: str) -> str:
    return max_length(not_blank(value, field="event_name"), field="event_name", max_len=255)

def validate_location(value: str) -> str:
    return max_length(not_blank(value, field="location"), field="location", max_len=500)

def validate_notes(value: str | None) -> str:
    return max_length((value or ""), field="notes", max_len=10_000)

def validate_attendees(value: int) -> int:
    return positive_int(value, field="attendees", min_=1)

def normalize_event_datetimes(start: datetime, end: datetime) -> tuple[datetime, datetime]:
    s = ensure_aware_utc(start, field="event_start")
    e = ensure_aware_utc(end,   field="event_end")
    ensure_order(s, e, field_start="event_start", field_end="event_end")
    return s, e