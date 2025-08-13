# tests/mappers/test_user_mappers.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

from enums.user_role import UserRole
from models.users import User
import services.mappers.user_mappers as um


@dataclass
class FakeUserModel:
    id: int | None = None
    username: str = ""
    email: str = ""
    role: str = "SUPPORT"
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    last_login: datetime | None = None
    date_joined: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    password_salt: bytes | None = None
    password_hash: bytes | None = None


def test_user_to_entity_and_back(monkeypatch):
    monkeypatch.setattr(um, "UserModel", FakeUserModel)

    now = datetime.now(timezone.utc)
    orm = FakeUserModel(
        id=7, username="support", email="support@epic.com", role="SUPPORT",
        is_active=True, is_staff=False, is_superuser=False,
        last_login=None, date_joined=now, created_at=now, updated_at=now
    )
    u = um.user_to_entity(orm)
    assert u.id == 7
    assert u.role == UserRole.SUPPORT
    assert u.email == "support@epic.com"

    # Aller-retour vers ORM
    orm2 = um.user_new_orm(u)
    assert isinstance(orm2, FakeUserModel)
    assert orm2.role == "SUPPORT"
    assert orm2.username == "support"


def test_user_apply(monkeypatch):
    monkeypatch.setattr(um, "UserModel", FakeUserModel)

    u = User.create(username="demo", email="demo@acme.com", role=UserRole.COMMERCIAL, password="Azerty123$")
    orm = um.user_new_orm(u)

    # On modifie quelques champs et applique
    u.set_role(UserRole.GESTION)
    u.clear_password()
    u.is_staff = True
    um.user_apply(orm, u)

    assert orm.role == "GESTION"
    assert orm.is_staff is True
    # mots de passe peuvent être None après clear_password()
    assert orm.password_salt is None and orm.password_hash is None