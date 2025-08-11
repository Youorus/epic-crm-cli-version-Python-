from typing import Optional, List

from models.users import User
from security.authorization import AuthContext, AuthzError, Role
from services.crud.user_repo import UserRepo

from services.db_session import session_scope


class UserService:
    """
    Gestion des collaborateurs (côté GESTION uniquement).
    Lecture: autorisée à tous (cahier des charges)
    Création / Mise à jour / Suppression : GESTION
    """

    def create(self, user: User, *, auth: AuthContext) -> User:
        if auth.role != Role.GESTION:
            raise AuthzError("Accès refusé : seul GESTION peut créer un collaborateur.")
        with session_scope() as s:
            return UserRepo(s).add(user)

    def get(self, user_id: int, *, auth: AuthContext) -> Optional[User]:
        # Lecture autorisée à tous
        with session_scope() as s:
            return UserRepo(s).get(user_id)

    def list(self, *, auth: AuthContext) -> List[User]:
        # Lecture autorisée à tous
        with session_scope() as s:
            return list(UserRepo(s).list())

    def update(self, user: User, *, auth: AuthContext) -> User:
        if auth.role != Role.GESTION:
            raise AuthzError("Accès refusé : seul GESTION peut modifier un collaborateur.")
        with session_scope() as s:
            return UserRepo(s).update(user)

    def delete(self, user_id: int, *, auth: AuthContext) -> None:
        if auth.role != Role.GESTION:
            raise AuthzError("Accès refusé : seul GESTION peut supprimer un collaborateur.")
        with session_scope() as s:
            UserRepo(s).delete(user_id)