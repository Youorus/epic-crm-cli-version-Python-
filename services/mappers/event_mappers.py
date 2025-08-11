from datetime import datetime

from models.event import Event
from orm.models import EventModel


def event_to_entity(o: EventModel) -> Event:
    return Event(
        id=o.id,
        contract_id=o.contract_id,
        client_id=o.client_id,
        support_contact_id=o.support_contact_id,
        event_name=o.event_name,
        event_start=datetime.fromisoformat(o.event_start),
        event_end=datetime.fromisoformat(o.event_end),
        location=o.location,
        attendees=o.attendees,
        notes=o.notes,
        created_at=datetime.fromisoformat(o.created_at),
        updated_at=datetime.fromisoformat(o.updated_at),
    )

def event_new_orm(e: Event) -> EventModel:
    return EventModel(
        contract_id=e.contract_id,
        client_id=e.client_id,
        support_contact_id=e.support_contact_id,
        event_name=e.event_name,
        event_start=e.event_start.isoformat(),
        event_end=e.event_end.isoformat(),
        location=e.location,
        attendees=e.attendees,
        notes=e.notes,
        created_at=e.created_at.isoformat(),
        updated_at=e.updated_at.isoformat(),
    )

def event_apply(orm: EventModel, e: Event) -> None:
    orm.contract_id = e.contract_id
    orm.client_id = e.client_id
    orm.support_contact_id = e.support_contact_id
    orm.event_name = e.event_name
    orm.event_start = e.event_start.isoformat()
    orm.event_end = e.event_end.isoformat()
    orm.location = e.location
    orm.attendees = e.attendees
    orm.notes = e.notes
    orm.updated_at = e.updated_at.isoformat()