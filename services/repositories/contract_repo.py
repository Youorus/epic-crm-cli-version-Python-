from models.contract import Contract
from orm.models import ContractModel
from services.base import OrmRepository
from services.mappers.contract_mappers import contract_to_entity, contract_new_orm, contract_apply


class ContractRepo(OrmRepository[ContractModel, Contract]):
    orm_cls = ContractModel
    to_entity = staticmethod(contract_to_entity)
    new_orm_from_entity = staticmethod(contract_new_orm)
    apply_entity = staticmethod(contract_apply)