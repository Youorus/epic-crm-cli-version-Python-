from enums.user_role import UserRole
from models.users import User
from datetime import datetime, date
from orm.models import UserModel


def user_to_entity(o: UserModel) -> User:
    u = User(
        id=o.id,
        username=o.username,
        email=o.email,
        role=UserRole(o.role),
        is_active=o.is_active,
        is_staff=o.is_staff,
        is_superuser=o.is_superuser,
        last_login=o.last_login,  # <-- Direct datetime ou None
        date_joined=o.date_joined,
        created_at=o.created_at,
        updated_at=o.updated_at,
    )
    # on ne mappe pas les secrets par défaut
    return u

def user_new_orm(e: User) -> UserModel:
    return UserModel(
        username=e.username,
        email=e.email,
        role=e.role.value,
        is_active=e.is_active,
        is_staff=e.is_staff,
        is_superuser=e.is_superuser,
        last_login=e.last_login,  # <-- PAS .isoformat()
        date_joined=e.date_joined,  # <-- datetime direct
        created_at=e.created_at,
        updated_at=e.updated_at,
        password_salt=e._password_salt,
        password_hash=e._password_hash,
    )

def user_apply(orm: UserModel, e: User) -> None:
    orm.username = e.username
    orm.email = e.email
    orm.role = e.role.value
    orm.is_active = e.is_active
    orm.is_staff = e.is_staff
    orm.is_superuser = e.is_superuser
    orm.last_login = e.last_login  # <-- datetime direct
    orm.updated_at = e.updated_at
    orm.password_salt = e._password_salt
    orm.password_hash = e._password_hash

