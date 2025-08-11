from __future__ import annotations

from typing import Optional, Iterable
from sqlalchemy.orm import Session

from models.users import User
from orm.models import UserModel
from services.base import OrmRepository
from services.mappers.user_mappers import user_to_entity, user_new_orm, user_apply


class UserRepo(OrmRepository[UserModel, User]):
    """
    Repository SQLAlchemy pour les utilisateurs.
    Hérite des opérations CRUD de base via OrmRepository et expose
    des méthodes de recherche usuelles (par email, username, ou les deux).
    """

    orm_cls = UserModel
    to_entity = staticmethod(user_to_entity)
    new_orm_from_entity = staticmethod(user_new_orm)
    apply_entity = staticmethod(user_apply)

    # --- Session shortcut (typing friendly) ---
    @property
    def session(self) -> Session:
        return self.s  # fourni par OrmRepository

    # --- Finders ---
    def get_by_id(self, user_id: int) -> Optional[User]:
        orm = self.session.get(self.orm_cls, user_id)
        return self.to_entity(orm) if orm else None

    def get_by_email(self, email: str) -> Optional[UserModel]:
        return (
            self.session.query(self.orm_cls)
            .filter(self.orm_cls.email == email)
            .one_or_none()
        )

    def get_by_username(self, username: str) -> Optional[UserModel]:
        return (
            self.session.query(self.orm_cls)
            .filter(self.orm_cls.username == username)
            .one_or_none()
        )

    def get_by_email_or_username(self, ident: str) -> Optional[UserModel]:
        return (
            self.session.query(self.orm_cls)
            .filter((self.orm_cls.email == ident) | (self.orm_cls.username == ident))
            .one_or_none()
        )

    def exists_by_email(self, email: str) -> bool:
        return self.session.query(self.session.query(self.orm_cls).filter_by(email=email).exists()).scalar() is True

    # --- Listing helpers ---
    def list_raw(self) -> Iterable[UserModel]:
        return self.session.query(self.orm_cls).all()

    def list(self) -> Iterable[User]:  # override to use efficient iteration
        for orm in self.session.query(self.orm_cls).all():
            yield self.to_entity(orm)