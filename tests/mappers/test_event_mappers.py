# tests/mappers/test_event_mappers.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from models.event import Event
import services.mappers.event_mappers as em


@dataclass
class FakeEventModel:
    id: int | None = None
    contract_id: int = 0
    client_id: int = 0
    support_contact_id: int | None = None
    event_name: str = ""
    event_start: datetime | None = None
    event_end: datetime | None = None
    location: str = ""
    attendees: int = 1
    notes: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


def test_event_to_entity_and_back(monkeypatch):
    monkeypatch.setattr(em, "EventModel", FakeEventModel)

    now = datetime.now(timezone.utc)
    orm = FakeEventModel(
        id=1, contract_id=10, client_id=11, support_contact_id=3,
        event_name="Kickoff", event_start=now, event_end=now + timedelta(hours=2),
        location="Paris", attendees=25, notes="Bring projector",
        created_at=now, updated_at=now
    )
    e = em.event_to_entity(orm)
    assert e.event_name == "Kickoff"
    assert e.duration_minutes == 120

    orm2 = em.event_new_orm(e)
    assert isinstance(orm2, FakeEventModel)
    assert orm2.event_name == "Kickoff"
    assert orm2.attendees == 25


def test_event_apply(monkeypatch):
    monkeypatch.setattr(em, "EventModel", FakeEventModel)

    e = Event.create(
        contract_id=99, client_id=77,
        event_name="Standup",
        event_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
        event_end=datetime(2025, 1, 1, 1, tzinfo=timezone.utc),
        location="Remote", attendees=5, notes="Daily"
    )
    orm = em.event_new_orm(e)
    e.rename("Daily Standup")
    e.set_attendees(6)
    e.update_notes("Scrum")
    em.event_apply(orm, e)
    assert orm.event_name == "Daily Standup"
    assert orm.attendees == 6
    assert orm.notes == "Scrum"