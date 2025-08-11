from models.clients import Client
from orm.models import ClientModel
from services.base import OrmRepository
from services.mappers.client_mappers import client_to_entity, client_new_orm, client_apply


class ClientRepo(OrmRepository[ClientModel, Client]):
    orm_cls = ClientModel
    to_entity = staticmethod(client_to_entity)
    new_orm_from_entity = staticmethod(client_new_orm)
    apply_entity = staticmethod(client_apply)