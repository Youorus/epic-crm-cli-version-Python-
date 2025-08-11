from services.repositories.contract_repo import ContractRepo
from typing import Iterable

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