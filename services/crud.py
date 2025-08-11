# services/usecases/crud.py
"""
Couche Use Cases pour exécuter des opérations CRUD sur chaque entité
en utilisant les repositories et le pattern Unit of Work.
"""

from typing import Iterable, Optional
from services.uow import session_scope

from services.repositories.user_repo import UserRepo
from services.repositories.client_repo import ClientRepo
from services.repositories.contract_repo import ContractRepo
from services.repositories.event_repo import EventRepo


# ——————————————————————————
# USER SERVICE
# ——————————————————————————
class UserService:
    def create(self, user) -> any:
        with session_scope() as s:
            return UserRepo(s).add(user)

    def get(self, user_id: int):
        with session_scope() as s:
            return UserRepo(s).get(user_id)

    def list(self) -> Iterable:
        with session_scope() as s:
            return list(UserRepo(s).list())

    def update(self, user):
        with session_scope() as s:
            return UserRepo(s).update(user)

    def delete(self, user_id: int) -> None:
        with session_scope() as s:
            UserRepo(s).delete(user_id)


# ——————————————————————————
# CLIENT SERVICE
# ——————————————————————————
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


# ——————————————————————————
# CONTRACT SERVICE
# ——————————————————————————
class ContractService:
    def create(self, contract) -> any:
        with session_scope() as s:
            return ContractRepo(s).add(contract)

    def get(self, contract_id: int):
        with session_scope() as s:
            return ContractRepo(s).get(contract_id)

    def list(self) -> Iterable:
        with session_scope() as s:
            return list(ContractRepo(s).list())

    def update(self, contract):
        with session_scope() as s:
            return ContractRepo(s).update(contract)

    def delete(self, contract_id: int) -> None:
        with session_scope() as s:
            ContractRepo(s).delete(contract_id)


# ——————————————————————————
# EVENT SERVICE
# ——————————————————————————
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