from services.repositories.client_repo import ClientRepo
from typing import Iterable

class ClientService:
    def create(self, client) -> any:
        with session_scope() as s:
            return ClientRepo(s).add(client)

    def get(self, client_id: int):
        with session_scope() as s:
            return ClientRepo(s).get(client_id)

    def list(self) -> Iterable:
        with session_scope() as s:
            return list(ClientRepo(s).list())

    def update(self, client):
        with session_scope() as s:
            return ClientRepo(s).update(client)

    def delete(self, client_id: int) -> None:
        with session_scope() as s:
            ClientRepo(s).delete(client_id)