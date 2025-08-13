# tests/test_events.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest

from models.event import Event


# ---------- Helpers ----------
UTC = timezone.utc

def _now():
    return datetime(2025, 1, 1, 12, 0, tzinfo=UTC)

def _valid_kwargs(**overrides):
    start = _now() + timedelta(hours=1)
    end = start + timedelta(hours=2)
    base = dict(
        contract_id=10,
        client_id=20,
        support_contact_id=None,
        event_name="Kickoff",
        event_start=start,
        event_end=end,
        location="Paris",
        attendees=50,
        notes="Bring slides",
    )
    base.update(overrides)
    return base


# ---------- Construction / validation ----------
def test_event_create_ok():
    e = Event.create(**_valid_kwargs())
    assert e.contract_id == 10
    assert e.client_id == 20
    assert e.support_contact_id is None
    assert e.event_name == "Kickoff"
    assert e.location == "Paris"
    assert e.attendees == 50
    assert e.event_start.tzinfo is UTC
    assert e.event_end.tzinfo is UTC
    assert e.event_end > e.event_start
    assert isinstance(e.created_at, datetime)
    assert isinstance(e.updated_at, datetime)


@pytest.mark.parametrize(
    "attendees",
    [0, -1]  # doit être >= 1
)
def test_invalid_attendees_raise(attendees):
    with pytest.raises(ValueError):
        Event(**_valid_kwargs(attendees=attendees))


def test_invalid_order_end_before_start_raises():
    start = _now() + timedelta(hours=3)
    end = _now() + timedelta(hours=2)
    with pytest.raises(ValueError):
        Event(**_valid_kwargs(event_start=start, event_end=end))


@pytest.mark.parametrize(
    "bad_name",
    ["", "  "]  # nom requis/non vide selon vos validateurs
)
def test_invalid_name_raises(bad_name):
    with pytest.raises(ValueError):
        Event(**_valid_kwargs(event_name=bad_name))


@pytest.mark.parametrize(
    "bad_location",
    ["", "  "]
)
def test_invalid_location_raises(bad_location):
    with pytest.raises(ValueError):
        Event(**_valid_kwargs(location=bad_location))


# ---------- Propriétés ----------
def test_duration_minutes_computed_ok():
    start = _now()
    end = start + timedelta(hours=1, minutes=15)  # 75 minutes
    e = Event(**_valid_kwargs(event_start=start, event_end=end))
    assert e.duration_minutes == 75


# ---------- Méthodes métier ----------
def test_touch_updates_updated_at():
    e = Event.create(**_valid_kwargs())
    before = e.updated_at
    # force à une valeur antérieure
    e.updated_at = before - timedelta(seconds=1)
    e.touch()
    assert e.updated_at > before


def test_rename_valid_and_touches():
    e = Event.create(**_valid_kwargs(event_name="Old"))
    before = e.updated_at
    e.rename("New Name")
    assert e.event_name == "New Name"
    assert e.updated_at >= before


def test_move_valid_and_touches():
    e = Event.create(**_valid_kwargs())
    before = e.updated_at
    ns = e.event_start + timedelta(days=1)
    ne = ns + timedelta(hours=2)
    e.move(new_start=ns, new_end=ne)
    assert e.event_start == ns
    assert e.event_end == ne
    assert e.updated_at >= before


def test_move_invalid_order_raises():
    e = Event.create(**_valid_kwargs())
    ns = e.event_start + timedelta(hours=2)
    ne = e.event_start + timedelta(minutes=30)  # avant ns
    with pytest.raises(ValueError):
        e.move(new_start=ns, new_end=ne)


def test_reschedule_with_timedelta_and_touches():
    e = Event.create(**_valid_kwargs())
    before_start, before_end = e.event_start, e.event_end
    e.reschedule(delta=timedelta(hours=3))
    assert e.event_start == before_start + timedelta(hours=3)
    assert e.event_end == before_end + timedelta(hours=3)
    # updated_at mis à jour
    assert e.updated_at >= e.created_at


def test_reschedule_with_non_timedelta_raises():
    e = Event.create(**_valid_kwargs())
    with pytest.raises(ValueError):
        e.reschedule(delta="3h")  # type: ignore[arg-type]


def test_change_location_and_touches():
    e = Event.create(**_valid_kwargs(location="Paris"))
    before = e.updated_at
    e.change_location("Lyon")
    assert e.location == "Lyon"
    assert e.updated_at >= before


def test_update_notes_and_touches():
    e = Event.create(**_valid_kwargs(notes="old"))
    before = e.updated_at
    e.update_notes("new note")
    assert e.notes == "new note"
    assert e.updated_at >= before


def test_set_attendees_and_touches():
    e = Event.create(**_valid_kwargs(attendees=10))
    before = e.updated_at
    e.set_attendees(250)
    assert e.attendees == 250
    assert e.updated_at >= before


def test_assign_support_contact_and_touches():
    e = Event.create(**_valid_kwargs(support_contact_id=None))
    before = e.updated_at
    e.assign_support_contact(7)
    assert e.support_contact_id == 7
    assert e.updated_at >= before


# ---------- Sérialisation / str ----------
def test_to_dict_shape_and_values():
    e = Event.create(**_valid_kwargs(contract_id=99, client_id=88, support_contact_id=7))
    d = e.to_dict()

    # clefs attendues
    assert {
        "id",
        "contract_id",
        "client_id",
        "support_contact_id",
        "event_name",
        "event_start",
        "event_end",
        "location",
        "attendees",
        "notes",
        "duration_minutes",
        "created_at",
        "updated_at",
    }.issubset(d.keys())

    assert d["contract_id"] == 99
    assert d["client_id"] == 88
    assert d["support_contact_id"] == 7
    assert isinstance(d["event_start"], str)
    assert isinstance(d["event_end"], str)
    assert isinstance(d["created_at"], str)
    assert isinstance(d["updated_at"], str)
    assert isinstance(d["duration_minutes"], int)


def test_str_representation_contains_name_location_and_start():
    e = Event.create(**_valid_kwargs(event_name="Demo", location="Nice"))
    s = str(e)
    assert "Demo" in s
    assert "Nice" in s
    # Isoformat du start
    assert e.event_start.isoformat() in s