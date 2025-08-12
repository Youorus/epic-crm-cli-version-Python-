# security/authorization.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Optional

from enums.user_role import UserRole
from models.users import User


class Role(str, Enum):
    COMMERCIAL = "COMMERCIAL"
    SUPPORT = "SUPPORT"
    GESTION = "GESTION"

@dataclass(frozen=True)
class AuthContext:
    """Contexte d’authentification porté partout dans l’app (CLI/UseCases)."""
    user_id: int
    role: Role

    def is_role(self, *roles: Role) -> bool:
        return self.role in roles

class _ClientLike(Protocol):
    id: Optional[int]
    sales_contact_id: Optional[int]

class _ContractLike(Protocol):
    id: Optional[int]
    client_id: int
    sales_contact_id: Optional[int]
    is_signed: bool

class _EventLike(Protocol):
    id: Optional[int]
    contract_id: int
    client_id: int
    support_contact_id: Optional[int]

class AuthzError(PermissionError):
    """Erreur d'autorisation (refus d'accès)."""

def can_read_clients(auth: AuthContext) -> bool:
    return auth.is_role(Role.GESTION, Role.COMMERCIAL, Role.SUPPORT)

def can_read_contracts(auth: AuthContext) -> bool:
    return auth.is_role(Role.GESTION, Role.COMMERCIAL, Role.SUPPORT)

def can_read_events(auth: AuthContext) -> bool:
    return auth.is_role(Role.GESTION, Role.COMMERCIAL, Role.SUPPORT)

def can_create_client(auth: AuthContext) -> bool:
    return auth.is_role(Role.GESTION, Role.COMMERCIAL)

def can_update_client(auth: AuthContext, *, client: _ClientLike) -> bool:
    if auth.is_role(Role.GESTION):
        return True
    if auth.is_role(Role.COMMERCIAL) and client.sales_contact_id == auth.user_id:
        return True
    return False

def can_delete_client(auth: AuthContext, *, client: _ClientLike) -> bool:
    return auth.is_role(Role.GESTION)

def can_create_contract(auth: AuthContext, **kwargs) -> bool:
    return auth.is_role(Role.GESTION)

def can_read_users(auth: AuthContext) -> bool:
    """
    Vérifie si l'utilisateur a le droit de lire la liste des utilisateurs.
    Règle métier :
    - Seul un utilisateur avec le rôle GESTION peut lire tous les utilisateurs.
    """
    return bool(auth and auth.is_role(Role.GESTION))

def can_update_contract(auth: AuthContext, *, contract: _ContractLike) -> bool:
    if auth.is_role(Role.GESTION):
        return True
    if auth.is_role(Role.COMMERCIAL) and contract.sales_contact_id == auth.user_id:
        return True
    return False

def can_delete_contract(auth: AuthContext, *, contract: _ContractLike) -> bool:
    return auth.is_role(Role.GESTION)

def can_create_event(auth: AuthContext, *, contract: _ContractLike) -> bool:
    if auth.is_role(Role.GESTION):
        return True
    if auth.is_role(Role.COMMERCIAL) and contract.is_signed and contract.sales_contact_id == auth.user_id:
        return True
    return False

def can_assign_support_to_event(auth: AuthContext) -> bool:
    return auth.is_role(Role.GESTION)

def can_update_event(auth: AuthContext, *, event: _EventLike, client: Optional[_ClientLike] = None) -> bool:
    if auth.is_role(Role.GESTION):
        return True
    if auth.is_role(Role.SUPPORT) and event.support_contact_id == auth.user_id:
        return True
    return False

def can_delete_event(auth: AuthContext, *, event: _EventLike) -> bool:
    return auth.is_role(Role.GESTION)

def filter_clients_for(auth: AuthContext, clients: list[_ClientLike]) -> list[_ClientLike]:
    if auth.is_role(Role.GESTION):
        return clients
    if auth.is_role(Role.COMMERCIAL):
        return [c for c in clients if c.sales_contact_id == auth.user_id]
    return clients  # SUPPORT : lecture de tous

def filter_contracts_for(auth: AuthContext, contracts: list[_ContractLike]) -> list[_ContractLike]:
    if auth.is_role(Role.GESTION):
        return contracts
    if auth.is_role(Role.COMMERCIAL):
        return [c for c in contracts if c.sales_contact_id == auth.user_id]
    return contracts  # SUPPORT : lecture de tous

def filter_events_for(auth: AuthContext, events: list[_EventLike]) -> list[_EventLike]:
    if auth.is_role(Role.GESTION):
        return events
    if auth.is_role(Role.SUPPORT):
        return [e for e in events if e.support_contact_id == auth.user_id]
    if auth.is_role(Role.COMMERCIAL):
        return events  # lecture autorisée par cahier des charges
    return []
def can_delete_user(
    auth: "AuthContext",
    *,
    user: Optional[User] = None,
    is_last_gestion: bool = False,
    forbid_superuser: bool = True,
) -> bool:
    """
    Règles de suppression d'un collaborateur (User) :

    - ✅ Seul le rôle GESTION peut supprimer des utilisateurs.
    - ❌ On ne peut pas se supprimer soi-même.
    - ❌ (optionnel) On empêche la suppression du *dernier* GESTION.
    - ❌ (optionnel) On empêche la suppression d'un superuser.

    Paramètres
    ----------
    auth : AuthContext
        Contexte de l'utilisateur courant.
    user : Optional[User]
        Cible à supprimer (si fournie, on applique les garde-fous spécifiques).
    is_last_gestion : bool
        Indique si `user` est le *dernier* compte avec rôle GESTION (calculé côté service).
    forbid_superuser : bool
        Interdire la suppression d'un superuser (par défaut True).

    Retour
    ------
    bool : True si la suppression est autorisée, False sinon.
    """
    # Seule la GESTION peut supprimer
    if not auth.is_role(Role.GESTION):
        return False

    # Sans cible précise : on autorise la suppression (vérifs faites côté service)
    if user is None:
        return True

    # Ne pas se supprimer soi-même
    if user.id is not None and user.id == auth.user_id:
        return False

    # Éviter la suppression du dernier GESTION
    if is_last_gestion and user.role == UserRole.GESTION:
        return False

    # Éviter la suppression d'un superuser (si activé)
    if forbid_superuser and getattr(user, "is_superuser", False):
        return False

    return True