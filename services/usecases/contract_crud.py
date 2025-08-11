from typing import Optional, List

from models.contract import Contract
from security.authorization import AuthContext, can_create_contract, AuthzError, can_read_contracts, \
    filter_contracts_for, can_update_contract, can_delete_contract
from services.crud.contract_repo import ContractRepo

from services.db_session import session_scope


class ContractService:
    """
    Lecture: autorisée à tous (cahier des charges).
    Création: GESTION uniquement.
    Modification: GESTION, ou COMMERCIAL propriétaire du contrat.
    Suppression: GESTION.
    """

    def create(self, contract: Contract, *, auth: AuthContext) -> Contract:
        # Besoin du client pour vérifier la règle si tu le souhaites (ici cdg: Gestion crée les contrats)
        if not can_create_contract(auth, client=None):  # client non nécessaire selon la règle actuelle
            raise AuthzError("Accès refusé : création de contrat interdite.")
        with session_scope() as s:
            return ContractRepo(s).add(contract)

    def get(self, contract_id: int, *, auth: AuthContext) -> Optional[Contract]:
        if not can_read_contracts(auth):
            raise AuthzError("Accès refusé.")
        with session_scope() as s:
            return ContractRepo(s).get(contract_id)

    def list(self, *, auth: AuthContext) -> List[Contract]:
        if not can_read_contracts(auth):
            raise AuthzError("Accès refusé.")
        with session_scope() as s:
            items = list(ContractRepo(s).list())
        return filter_contracts_for(auth, items)

    def update(self, contract: Contract, *, auth: AuthContext) -> Optional[Contract]:
        with session_scope() as s:
            repo = ContractRepo(s)
            existing = repo.get(contract.id)  # type: ignore[arg-type]
            if not existing:
                return None
            if not can_update_contract(auth, contract=existing):
                raise AuthzError("Accès refusé : modification contrat interdite.")
            return repo.update(contract)

    def delete(self, contract_id: int, *, auth: AuthContext) -> None:
        with session_scope() as s:
            repo = ContractRepo(s)
            existing = repo.get(contract_id)
            if not existing:
                return
            if not can_delete_contract(auth, contract=existing):
                raise AuthzError("Accès refusé : suppression contrat interdite.")
            repo.delete(contract_id)

