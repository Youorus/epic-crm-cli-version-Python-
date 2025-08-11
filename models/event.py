from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from validators.event_validators import (
    validate_event_name,
    validate_event_location,
    validate_event_attendees,
    validate_event_notes,
    validate_event_start,
    validate_event_end,
    validate_event_order,
)

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(slots=True)
class Event:
    # Liens (IDs int)
    contract_id: int
    client_id: int
    support_contact_id: Optional[int] = None

    # Données d’évènement
    event_name: str = field(default="")
    event_start: datetime = field(default_factory=_utcnow)
    event_end: datetime = field(default_factory=_utcnow)
    location: str = field(default="")
    attendees: int = field(default=1)
    notes: str = field(default="")

    # Techniques
    id: Optional[int] = None
    created_at: datetime = field(default_factory=_utcnow, kw_only=True)
    updated_at: datetime = field(default_factory=_utcnow, kw_only=True)

    def __post_init__(self) -> None:
        self.event_name = validate_event_name(self.event_name)
        self.location = validate_event_location(self.location)
        self.attendees = validate_event_attendees(self.attendees)
        self.notes = validate_event_notes(self.notes)
        self.event_start = validate_event_start(self.event_start)
        self.event_end = validate_event_end(self.event_end)
        validate_event_order(self.event_start, self.event_end)

    @property
    def duration_minutes(self) -> int:
        return int((self.event_end - self.event_start).total_seconds() // 60)

    # Métier
    def touch(self) -> None:
        self.updated_at = _utcnow()

    def rename(self, new_name: str) -> None:
        self.event_name = validate_event_name(new_name)
        self.touch()

    def move(self, *, new_start: datetime, new_end: datetime) -> None:
        ns = validate_event_start(new_start)
        ne = validate_event_end(new_end)
        validate_event_order(ns, ne)
        self.event_start, self.event_end = ns, ne
        self.touch()

    def reschedule(self, *, delta: timedelta) -> None:
        if not isinstance(delta, timedelta):
            raise ValueError("delta doit être un timedelta.")
        self.event_start = validate_event_start(self.event_start + delta)
        self.event_end = validate_event_end(self.event_end + delta)
        self.touch()

    def change_location(self, new_location: str) -> None:
        self.location = validate_event_location(new_location)
        self.touch()

    def update_notes(self, new_notes: str) -> None:
        self.notes = validate_event_notes(new_notes)
        self.touch()

    def set_attendees(self, n: int) -> None:
        self.attendees = validate_event_attendees(n)
        self.touch()

    def assign_support_contact(self, user_id: Optional[int]) -> None:
        self.support_contact_id = user_id
        self.touch()

    # Sérialisation
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "client_id": self.client_id,
            "support_contact_id": self.support_contact_id,
            "event_name": self.event_name,
            "event_start": self.event_start.isoformat(),
            "event_end": self.event_end.isoformat(),
            "location": self.location,
            "attendees": self.attendees,
            "notes": self.notes,
            "duration_minutes": self.duration_minutes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def create(
        cls,
        *,
        contract_id: int,
        client_id: int,
        event_name: str,
        event_start: datetime,
        event_end: datetime,
        location: str,
        attendees: int,
        support_contact_id: Optional[int] = None,
        notes: str = "",
    ) -> "Event":
        return cls(
            contract_id=contract_id,
            client_id=client_id,
            support_contact_id=support_contact_id,
            event_name=event_name,
            event_start=event_start,
            event_end=event_end,
            location=location,
            attendees=attendees,
            notes=notes,
        )

    def __str__(self) -> str:
        return f"{self.event_name} ({self.location}) — {self.event_start.isoformat()}"