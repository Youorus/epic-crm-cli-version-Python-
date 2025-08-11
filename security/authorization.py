# security/authorization.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Optional

# —————————————————————————————————————————
# Rôles & contexte d’authentification
# —————————————————————————————————————————

class Role(str, Enum):
    COMMERCIAL = "COMMERCIAL"
    SUPPORT = "SUPPORT"
    GESTION = "GESTION"


@dataclass(frozen=True)
class AuthContext:
    """Contexte porté par le JWT (ou équivalent dans ton app CLI)."""
    user_id: int
    role: Role

    def is_role(self, *roles: Role) -> bool:
        return self.role in roles


# —————————————————————————————————————————
# Protocols (interfaces minimales des ressources)
# —————————————————————————————————————————

class _ClientLike(Protocol):
    id: Optional[int]
    sales_contact_id: Optional[int]  # commercial propriétaire


class _ContractLike(Protocol):
    id: Optional[int]
    client_id: int
    sales_contact_id: Optional[int]  # commercial propriétaire du contrat (souvent = client.sales_contact_id)
    is_signed: bool


class _EventLike(Protocol):
    id: Optional[int]
    contract_id: int
    client_id: int
    support_contact_id: Optional[int]  # technicien support responsable


# —————————————————————————————————————————
# Exceptions
# —————————————————————————————————————————

class AuthzError(PermissionError):
    """Erreur d'autorisation (refus d'accès)."""


# —————————————————————————————————————————
# Règles de base (lecture)
# —————————————————————————————————————————
# Cahier des charges: "Tous les collaborateurs doivent pouvoir accéder à tous
# les clients, contrats et événements en lecture seule."

def can_read_clients(auth: AuthContext) -> bool:
    return auth.is_role(Role.GESTION, Role.COMMERCIAL, Role.SUPPORT)

def can_read_contracts(auth: AuthContext) -> bool:
    return auth.is_role(Role.GESTION, Role.COMMERCIAL, Role.SUPPORT)

def can_read_events(auth: AuthContext) -> bool:
    return auth.is_role(Role.GESTION, Role.COMMERCIAL, Role.SUPPORT)


# —————————————————————————————————————————
# Clients
# —————————————————————————————————————————
# Gestion : peut tout faire
# Commercial : peut créer des clients (auto-association), et modifier SEULEMENT ses clients
# Support : lecture seule

def can_create_client(auth: AuthContext) -> bool:
    return auth.is_role(Role.GESTION, Role.COMMERCIAL)

def can_update_client(auth: AuthContext, *, client: _ClientLike) -> bool:
    if auth.is_role(Role.GESTION):
        return True
    if auth.is_role(Role.COMMERCIAL) and client.sales_contact_id == auth.user_id:
        return True
    return False

def can_delete_client(auth: AuthContext, *, client: _ClientLike) -> bool:
    # Suppression : seulement gestion (moindre privilège)
    return auth.is_role(Role.GESTION)


# —————————————————————————————————————————
# Contrats
# —————————————————————————————————————————
# Gestion : crée & modifie TOUS les contrats
# Commercial : peut modifier les contrats des clients DONT IL EST RESPONSABLE
# Support : lecture seule

# Le cahier des charges dit : "un collaborateur du département gestion crée un contrat"
def can_create_contract(auth: AuthContext) -> bool:
    return auth.is_role(Role.GESTION)

def can_update_contract(auth: AuthContext, *, contract: _ContractLike) -> bool:
    if auth.is_role(Role.GESTION):
        return True
    if auth.is_role(Role.COMMERCIAL) and contract.sales_contact_id == auth.user_id:
        return True
    return False

def can_delete_contract(auth: AuthContext, *, contract: _ContractLike) -> bool:
    return auth.is_role(Role.GESTION)


# —————————————————————————————————————————
# Événements
# —————————————————————————————————————————
# Processus :
# - Contrat signé -> le COMMERCIAL crée l'événement pour son client
# - Le département GESTION assigne un SUPPORT responsable
# - SUPPORT peut mettre à jour les événements DONT IL EST RESPONSABLE
# - GESTION peut modifier tous les événements
# - COMMERCIAL : création (si contrat signé & il est propriétaire), puis lecture seule

def can_create_event(
    auth: AuthContext,
    *,
    contract: _ContractLike,
) -> bool:
    if auth.is_role(Role.GESTION):
        return True
    if auth.is_role(Role.COMMERCIAL) and contract.is_signed and contract.sales_contact_id == auth.user_id:
        return True
    return False

def can_assign_support_to_event(auth: AuthContext) -> bool:
    # Cahier : "le département gestion désigne un membre du support"
    return auth.is_role(Role.GESTION)

def can_update_event(
    auth: AuthContext,
    *,
    event: _EventLike,
    client: Optional[_ClientLike] = None,  # facultatif si tu veux recouper côté client
) -> bool:
    if auth.is_role(Role.GESTION):
        return True
    if auth.is_role(Role.SUPPORT) and event.support_contact_id == auth.user_id:
        return True
    # Commercial n'a pas de droit explicite de modification après création -> refuser.
    return False

def can_delete_event(auth: AuthContext, *, event: _EventLike) -> bool:
    return auth.is_role(Role.GESTION)


# —————————————————————————————————————————
# Helpers de filtrage (pour le moindre privilège côté "list")
# —————————————————————————————————————————

def filter_clients_for(auth: AuthContext, clients: list[_ClientLike]) -> list[_ClientLike]:
    """
    Applique le principe de moindre privilège sur une liste de clients.
    - GESTION : tous
    - COMMERCIAL : uniquement ses clients
    - SUPPORT : tous (lecture seule autorisée) -> mais on peut laisser tous si strictement lecture
    """
    if auth.is_role(Role.GESTION):
        return clients
    if auth.is_role(Role.COMMERCIAL):
        return [c for c in clients if c.sales_contact_id == auth.user_id]
    # SUPPORT : lecture seule sur tous. Si tu veux restreindre l'énumération, filtre ici.
    return clients

def filter_contracts_for(auth: AuthContext, contracts: list[_ContractLike]) -> list[_ContractLike]:
    if auth.is_role(Role.GESTION):
        return contracts
    if auth.is_role(Role.COMMERCIAL):
        return [c for c in contracts if c.sales_contact_id == auth.user_id]
    # SUPPORT : lecture seule sur tous
    return contracts

def filter_events_for(
    auth: AuthContext,
    events: list[_EventLike],
) -> list[_EventLike]:
    if auth.is_role(Role.GESTION):
        return events
    if auth.is_role(Role.SUPPORT):
        return [e for e in events if e.support_contact_id == auth.user_id]
    if auth.is_role(Role.COMMERCIAL):
        # Le cahier des charges ne précise pas de restriction stricte d'énumération
        # pour les commerciaux sur les événements : lecture seule autorisée sur tous.
        # Si tu veux restreindre à "leurs" clients, applique un join côté repo
        # ou passe une fonction de prédicat basée sur client_id.
        return events
    return []  # rôle inconnu -> rien