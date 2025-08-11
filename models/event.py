from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

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
        self.event_name = max_length(not_blank(self.event_name, field="event_name"), field="event_name", max_len=255)
        self.location   = max_length(not_blank(self.location,   field="location"),   max_len=500, field="location")
        self.attendees  = positive_int(self.attendees, field="attendees", min_=1)
        # notes: facultatif, bornons à 10k chars
        self.notes = max_length(self.notes or "", field="notes", max_len=10_000)

        self.event_start = ensure_aware_utc(self.event_start, field="event_start")
        self.event_end   = ensure_aware_utc(self.event_end,   field="event_end")
        ensure_order(self.event_start, self.event_end, field_start="event_start", field_end="event_end")

    @property
    def duration_minutes(self) -> int:
        return int((self.event_end - self.event_start).total_seconds() // 60)

    # Métier
    def touch(self) -> None:
        self.updated_at = _utcnow()

    def rename(self, new_name: str) -> None:
        self.event_name = max_length(not_blank(new_name, field="event_name"), field="event_name", max_len=255)
        self.touch()

    def move(self, *, new_start: datetime, new_end: datetime) -> None:
        ns = ensure_aware_utc(new_start, field="new_start")
        ne = ensure_aware_utc(new_end,   field="new_end")
        ensure_order(ns, ne, field_start="new_start", field_end="new_end")
        self.event_start, self.event_end = ns, ne
        self.touch()

    def reschedule(self, *, delta: timedelta) -> None:
        if not isinstance(delta, timedelta):
            raise ValueError("delta doit être un timedelta.")
        self.event_start = ensure_aware_utc(self.event_start + delta, field="event_start")
        self.event_end   = ensure_aware_utc(self.event_end + delta,   field="event_end")
        self.touch()

    def change_location(self, new_location: str) -> None:
        self.location = max_length(not_blank(new_location, field="location"), field="location", max_len=500)
        self.touch()

    def update_notes(self, new_notes: str) -> None:
        self.notes = max_length(new_notes or "", field="notes", max_len=10_000)
        self.touch()

    def set_attendees(self, n: int) -> None:
        self.attendees = positive_int(n, field="attendees", min_=1)
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