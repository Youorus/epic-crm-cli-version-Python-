from models.users import User
from orm.models import UserModel
from services.base import OrmRepository
from services.mappers.user_mappers import user_to_entity, user_new_orm, user_apply


class UserRepo(OrmRepository[UserModel, User]):
    orm_cls = UserModel
    to_entity = staticmethod(user_to_entity)
    new_orm_from_entity = staticmethod(user_new_orm)
    apply_entity = staticmethod(user_apply)