from typing import Optional, List

from models.event import Event
from security.authorization import AuthContext, can_create_event, AuthzError, can_read_events, filter_events_for, \
    can_delete_event, can_assign_support_to_event, can_update_event
from services.crud.contract_repo import ContractRepo
from services.crud.event_repo import EventRepo

from services.db_session import session_scope


class EventService:
    """
    Lecture: autorisée à tous (cahier des charges).
    Création: GESTION, ou COMMERCIAL propriétaire si contrat signé.
    Modification: GESTION, ou SUPPORT assigné à l’événement.
    Suppression: GESTION.
    Assignation du support: GESTION.
    """

    def create(self, event: Event, *, auth: AuthContext) -> Event:
        with session_scope() as s:
            contracts = ContractRepo(s)
            contract = contracts.get(event.contract_id)
            if not contract:
                raise ValueError("Contrat introuvable pour cet événement.")
            if not can_create_event(auth, contract=contract):
                raise AuthzError("Accès refusé : création d'événement interdite.")
            return EventRepo(s).add(event)

    def get(self, event_id: int, *, auth: AuthContext) -> Optional[Event]:
        if not can_read_events(auth):
            raise AuthzError("Accès refusé.")
        with session_scope() as s:
            return EventRepo(s).get(event_id)

    def list(self, *, auth: AuthContext) -> List[Event]:
        if not can_read_events(auth):
            raise AuthzError("Accès refusé.")
        with session_scope() as s:
            items = list(EventRepo(s).list())
        return filter_events_for(auth, items)

    def update(self, event: Event, *, auth: AuthContext) -> Optional[Event]:
        with session_scope() as s:
            erepo = EventRepo(s)
            existing = erepo.get(event.id)  # type: ignore[arg-type]
            if not existing:
                return None
            # Optionnel : récupérer le client si tu souhaites croiser (non requis ici)
            if not can_update_event(auth, event=existing, client=None):
                raise AuthzError("Accès refusé : modification événement interdite.")
            return erepo.update(event)

    def delete(self, event_id: int, *, auth: AuthContext) -> None:
        with session_scope() as s:
            erepo = EventRepo(s)
            existing = erepo.get(event_id)
            if not existing:
                return
            if not can_delete_event(auth, event=existing):
                raise AuthzError("Accès refusé : suppression événement interdite.")
            erepo.delete(event_id)

    def assign_support(self, *, event_id: int, support_user_id: int, auth: AuthContext) -> Optional[Event]:
        """GESTION assigne (ou réassigne) un responsable support à l’événement."""
        if not can_assign_support_to_event(auth):
            raise AuthzError("Accès refusé : seul GESTION peut assigner le support.")
        with session_scope() as s:
            erepo = EventRepo(s)
            existing = erepo.get(event_id)
            if not existing:
                return None
            existing.assign_support_contact(support_user_id)
            return erepo.update(existing)