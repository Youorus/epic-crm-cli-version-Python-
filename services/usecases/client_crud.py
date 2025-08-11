from typing import Optional, List

from models.clients import Client
from security.authorization import can_create_client, AuthzError, AuthContext, can_read_clients, filter_clients_for, \
    can_update_client, can_delete_client, Role
from services.crud.client_repo import ClientRepo

from services.db_session import session_scope


class ClientService:
    """
    Lecture: autorisée à tous (cahier des charges).
    Création: GESTION ou COMMERCIAL (commercial auto-assigné).
    Modification: GESTION, ou COMMERCIAL propriétaire du client.
    Suppression: GESTION.
    """

    def create(self, client: Client, *, auth: AuthContext) -> Client:
        if not can_create_client(auth):
            raise AuthzError("Accès refusé : création de client interdite.")
        # Auto-assignation pour un commercial
        if auth.role == Role.COMMERCIAL and client.sales_contact_id is None:
            client.sales_contact_id = auth.user_id
        with session_scope() as s:
            return ClientRepo(s).add(client)

    def get(self, client_id: int, *, auth: AuthContext) -> Optional[Client]:
        if not can_read_clients(auth):
            raise AuthzError("Accès refusé.")
        with session_scope() as s:
            return ClientRepo(s).get(client_id)

    def list(self, *, auth: AuthContext) -> List[Client]:
        if not can_read_clients(auth):
            raise AuthzError("Accès refusé.")
        with session_scope() as s:
            items = list(ClientRepo(s).list())
        return filter_clients_for(auth, items)

    def update(self, client: Client, *, auth: AuthContext) -> Optional[Client]:
        with session_scope() as s:
            repo = ClientRepo(s)
            existing = repo.get(client.id)  # type: ignore[arg-type]
            if not existing:
                return None
            if not can_update_client(auth, client=existing):
                raise AuthzError("Accès refusé : modification client interdite.")
            return repo.update(client)

    def delete(self, client_id: int, *, auth: AuthContext) -> None:
        with session_scope() as s:
            repo = ClientRepo(s)
            existing = repo.get(client_id)
            if not existing:
                return
            if not can_delete_client(auth, client=existing):
                raise AuthzError("Accès refusé : suppression client interdite.")
            repo.delete(client_id)
