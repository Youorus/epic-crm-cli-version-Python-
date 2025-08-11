from services.repositories.event_repo import EventRepo
from typing import Iterable

class EventService:
    def create(self, event) -> any:
        with session_scope() as s:
            return EventRepo(s).add(event)

    def get(self, event_id: int):
        with session_scope() as s:
            return EventRepo(s).get(event_id)

    def list(self) -> Iterable:
        with session_scope() as s:
            return list(EventRepo(s).list())

    def update(self, event):
        with session_scope() as s:
            return EventRepo(s).update(event)

    def delete(self, event_id: int) -> None:
        with session_scope() as s:
            EventRepo(s).delete(event_id)