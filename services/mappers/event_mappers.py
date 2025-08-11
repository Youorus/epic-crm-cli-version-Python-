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
        event_start=o.event_start,
        event_end=o.event_end,
        location=o.location,
        attendees=o.attendees,
        notes=o.notes,
        created_at=o.created_at,
        updated_at=o.updated_at,
    )

def event_new_orm(e: Event) -> EventModel:
    return EventModel(
        contract_id=e.contract_id,
        client_id=e.client_id,
        support_contact_id=e.support_contact_id,
        event_name=e.event_name,
        event_start=e.event_start,  # <-- datetime direct
        event_end=e.event_end,  # <-- datetime direct
        location=e.location,
        attendees=e.attendees,
        notes=e.notes,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )

def event_apply(orm: EventModel, e: Event) -> None:
    orm.contract_id = e.contract_id
    orm.client_id = e.client_id
    orm.support_contact_id = e.support_contact_id
    orm.event_name = e.event_name
    orm.event_start = e.event_start
    orm.event_end = e.event_end
    orm.location = e.location
    orm.attendees = e.attendees
    orm.notes = e.notes
    orm.updated_at = e.updated_at