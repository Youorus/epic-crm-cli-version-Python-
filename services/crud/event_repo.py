from models.event import Event
from orm.models import EventModel
from services.base import OrmRepository
from services.mappers.event_mappers import event_to_entity, event_new_orm, event_apply


class EventRepo(OrmRepository[EventModel, Event]):
    orm_cls = EventModel
    to_entity = staticmethod(event_to_entity)
    new_orm_from_entity = staticmethod(event_new_orm)
    apply_entity = staticmethod(event_apply)