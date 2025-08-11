from services.repositories.user_repo import UserRepo
from typing import Iterable

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