# src/your_app/domain/validators/event_validators.py
from __future__ import annotations
from datetime import datetime

from validators.validators import (
    not_blank,
    max_length,
    positive_int,
    ensure_aware_utc,
    ensure_order,
)

# --- Libellés & texte ---
def validate_event_name(value: str) -> str:
    return max_length(not_blank(value, field="event_name"), field="event_name", max_len=255)

def validate_event_location(value: str) -> str:
    return max_length(not_blank(value, field="location"), field="location", max_len=500)

def validate_event_notes(value: str | None) -> str:
    return max_length((value or ""), field="notes", max_len=10_000)

# --- Participants ---
def validate_event_attendees(value: int) -> int:
    return positive_int(value, field="attendees", min_=1)

# --- Dates ---
def validate_event_start(dt: datetime) -> datetime:
    return ensure_aware_utc(dt, field="event_start")

def validate_event_end(dt: datetime) -> datetime:
    return ensure_aware_utc(dt, field="event_end")

def validate_event_order(start: datetime, end: datetime) -> None:
    ensure_order(start, end, field_start="event_start", field_end="event_end")

def normalize_event_datetimes(start: datetime, end: datetime) -> tuple[datetime, datetime]:
    s = validate_event_start(start)
    e = validate_event_end(end)
    validate_event_order(s, e)
    return s, e