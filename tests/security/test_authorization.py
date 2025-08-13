# tests/test_authorization.py
from __future__ import annotations

import dataclasses
import pytest

from security.authorization import (
    Role,
    AuthContext,
    can_read_clients,
    can_read_contracts,
    can_read_events,
    can_create_client,
    can_update_client,
    can_delete_client,
    can_create_contract,
    can_update_contract,
    can_delete_contract,
    can_create_event,
    can_assign_support_to_event,
    can_update_event,
    can_delete_event,
    can_read_users,
    filter_clients_for,
    filter_contracts_for,
    filter_events_for,
    can_delete_user,
)
from enums.user_role import UserRole
from models.users import User


# ─────────────────────────────────────────────────────────
# Doubles simples qui respectent les Protocols _ClientLike/_ContractLike/_EventLike
# ─────────────────────────────────────────────────────────
@dataclasses.dataclass
class DummyClient:
    id: int | None
    sales_contact_id: int | None


@dataclasses.dataclass
class DummyContract:
    id: int | None
    client_id: int
    sales_contact_id: int | None
    is_signed: bool


@dataclasses.dataclass
class DummyEvent:
    id: int | None
    contract_id: int
    client_id: int
    support_contact_id: int | None


# ─────────────────────────────────────────────────────────
# Fixtures Auth
# ─────────────────────────────────────────────────────────
@pytest.fixture
def auth_gestion() -> AuthContext:
    return AuthContext(user_id=1, role=Role.GESTION)


@pytest.fixture
def auth_commercial() -> AuthContext:
    return AuthContext(user_id=2, role=Role.COMMERCIAL)


@pytest.fixture
def auth_support() -> AuthContext:
    return AuthContext(user_id=3, role=Role.SUPPORT)


# ─────────────────────────────────────────────────────────
# Sanity checks de base
# ─────────────────────────────────────────────────────────
def test_role_enum_values():
    assert Role.GESTION.value == "GESTION"
    assert Role.COMMERCIAL.value == "COMMERCIAL"
    assert Role.SUPPORT.value == "SUPPORT"


def test_authcontext_is_role(auth_gestion, auth_commercial):
    assert auth_gestion.is_role(Role.GESTION)
    assert not auth_gestion.is_role(Role.SUPPORT)
    assert auth_commercial.is_role(Role.COMMERCIAL, Role.SUPPORT)


# ─────────────────────────────────────────────────────────
# Lecture (clients / contrats / événements / user)
# ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("role", [Role.GESTION, Role.COMMERCIAL, Role.SUPPORT])
def test_can_read_clients_contracts_events(role):
    auth = AuthContext(user_id=42, role=role)
    assert can_read_clients(auth) is True
    assert can_read_contracts(auth) is True
    assert can_read_events(auth) is True


def test_can_read_users_only_gestion(auth_gestion, auth_commercial, auth_support):
    assert can_read_users(auth_gestion) is True
    assert can_read_users(auth_commercial) is False
    assert can_read_users(auth_support) is False


# ─────────────────────────────────────────────────────────
# Clients — création / update / delete
# ─────────────────────────────────────────────────────────
def test_can_create_client_gestion_or_commercial(auth_gestion, auth_commercial, auth_support):
    assert can_create_client(auth_gestion) is True
    assert can_create_client(auth_commercial) is True
    assert can_create_client(auth_support) is False


def test_can_update_client_rules(auth_gestion, auth_commercial, auth_support):
    # client possédé par le commercial #2
    c = DummyClient(id=10, sales_contact_id=2)

    assert can_update_client(auth_gestion, client=c) is True         # GESTION : toujours OK
    assert can_update_client(auth_commercial, client=c) is True      # propriétaire
    assert can_update_client(auth_support, client=c) is False        # SUPPORT jamais


def test_can_delete_client_only_gestion(auth_gestion, auth_commercial):
    c = DummyClient(id=11, sales_contact_id=None)
    assert can_delete_client(auth_gestion, client=c) is True
    assert can_delete_client(auth_commercial, client=c) is False


# ─────────────────────────────────────────────────────────
# Contrats — création / update / delete
# ─────────────────────────────────────────────────────────
def test_can_create_contract_only_gestion(auth_gestion, auth_commercial, auth_support):
    # can_create_contract ignore **kwargs selon votre signature
    assert can_create_contract(auth_gestion) is True
    assert can_create_contract(auth_commercial) is False
    assert can_create_contract(auth_support) is False


def test_can_update_contract_rules(auth_gestion, auth_commercial, auth_support):
    # contrat possédé par le commercial #2
    ct = DummyContract(id=100, client_id=10, sales_contact_id=2, is_signed=False)

    assert can_update_contract(auth_gestion, contract=ct) is True
    assert can_update_contract(auth_commercial, contract=ct) is True
    assert can_update_contract(auth_support, contract=ct) is False


def test_can_delete_contract_only_gestion(auth_gestion, auth_commercial):
    ct = DummyContract(id=101, client_id=10, sales_contact_id=None, is_signed=False)
    assert can_delete_contract(auth_gestion, contract=ct) is True
    assert can_delete_contract(auth_commercial, contract=ct) is False


# ─────────────────────────────────────────────────────────
# Événements — création / update / delete / assignation
# ─────────────────────────────────────────────────────────
def test_can_create_event_rules(auth_gestion, auth_commercial, auth_support):
    signed_owned = DummyContract(id=1, client_id=1, sales_contact_id=auth_commercial.user_id, is_signed=True)
    unsigned_owned = dataclasses.replace(signed_owned, is_signed=False)
    signed_other = dataclasses.replace(signed_owned, sales_contact_id=999)

    # GESTION : toujours OK
    assert can_create_event(auth_gestion, contract=signed_owned) is True
    assert can_create_event(auth_gestion, contract=unsigned_owned) is True

    # COMMERCIAL : uniquement si signé + propriétaire
    assert can_create_event(auth_commercial, contract=signed_owned) is True
    assert can_create_event(auth_commercial, contract=unsigned_owned) is False
    assert can_create_event(auth_commercial, contract=signed_other) is False

    # SUPPORT : jamais
    assert can_create_event(auth_support, contract=signed_owned) is False


def test_can_assign_support_only_gestion(auth_gestion, auth_support):
    assert can_assign_support_to_event(auth_gestion) is True
    assert can_assign_support_to_event(auth_support) is False


def test_can_update_event_rules(auth_gestion, auth_support):
    # Événement assigné au support #3
    ev = DummyEvent(id=50, contract_id=1, client_id=1, support_contact_id=3)

    assert can_update_event(auth_gestion, event=ev, client=None) is True
    assert can_update_event(auth_support, event=ev, client=None) is True

    # Un autre support ne peut pas
    other_support = AuthContext(user_id=999, role=Role.SUPPORT)
    assert can_update_event(other_support, event=ev, client=None) is False


def test_can_delete_event_only_gestion(auth_gestion, auth_support):
    ev = DummyEvent(id=51, contract_id=1, client_id=1, support_contact_id=None)
    assert can_delete_event(auth_gestion, event=ev) is True
    assert can_delete_event(auth_support, event=ev) is False


# ─────────────────────────────────────────────────────────
# Filtres (sélection par rôle)
# ─────────────────────────────────────────────────────────
def test_filter_clients_for_rules(auth_gestion, auth_commercial, auth_support):
    all_clients = [
        DummyClient(id=1, sales_contact_id=2),
        DummyClient(id=2, sales_contact_id=999),
        DummyClient(id=3, sales_contact_id=None),
    ]
    # GESTION voit tout
    assert filter_clients_for(auth_gestion, all_clients) == all_clients
    # COMMERCIAL ne voit que ses clients
    filtered = filter_clients_for(auth_commercial, all_clients)
    assert [c.id for c in filtered] == [1]
    # SUPPORT voit tout (lecture libre)
    assert filter_clients_for(auth_support, all_clients) == all_clients


def test_filter_contracts_for_rules(auth_gestion, auth_commercial, auth_support):
    all_contracts = [
        DummyContract(id=10, client_id=1, sales_contact_id=2, is_signed=True),
        DummyContract(id=11, client_id=2, sales_contact_id=999, is_signed=False),
    ]
    assert filter_contracts_for(auth_gestion, all_contracts) == all_contracts
    filtered = filter_contracts_for(auth_commercial, all_contracts)
    assert [c.id for c in filtered] == [10]
    # SUPPORT : lecture de tous
    assert filter_contracts_for(auth_support, all_contracts) == all_contracts


def test_filter_events_for_rules(auth_gestion, auth_commercial, auth_support):
    all_events = [
        DummyEvent(id=20, contract_id=1, client_id=1, support_contact_id=3),
        DummyEvent(id=21, contract_id=2, client_id=2, support_contact_id=None),
    ]
    # GESTION : tout
    assert filter_events_for(auth_gestion, all_events) == all_events
    # SUPPORT : uniquement ceux assignés à lui-même (#3)
    mine = filter_events_for(auth_support, all_events)
    assert [e.id for e in mine] == [20]
    # COMMERCIAL : lecture autorisée (cahier des charges) → tout
    assert filter_events_for(AuthContext(2, Role.COMMERCIAL), all_events) == all_events


# ─────────────────────────────────────────────────────────
# can_delete_user — cas métiers
# ─────────────────────────────────────────────────────────
def _make_user(uid: int, role: UserRole, **flags) -> User:
    """Crée un User domaine léger pour les tests."""
    u = User.create(username=f"user{uid}", email=f"user{uid}@example.com", role=role)
    u.id = uid
    for k, v in flags.items():
        setattr(u, k, v)
    return u


def test_can_delete_user_basic_rules(auth_gestion):
    target = _make_user(10, UserRole.SUPPORT)
    assert can_delete_user(auth_gestion, user=target) is True


def test_can_delete_user_only_gestion():
    target = _make_user(10, UserRole.SUPPORT)
    auth = AuthContext(user_id=2, role=Role.COMMERCIAL)
    assert can_delete_user(auth, user=target) is False


def test_can_delete_user_cannot_delete_self(auth_gestion):
    me = _make_user(auth_gestion.user_id, UserRole.GESTION)
    assert can_delete_user(auth_gestion, user=me) is False


def test_can_delete_user_last_gestion_block(auth_gestion):
    last_manager = _make_user(10, UserRole.GESTION)
    assert can_delete_user(auth_gestion, user=last_manager, is_last_gestion=True) is False
    # si ce n'est pas le dernier, c'est OK
    assert can_delete_user(auth_gestion, user=last_manager, is_last_gestion=False) is True


def test_can_delete_user_forbid_superuser_flag(auth_gestion):
    boss = _make_user(99, UserRole.GESTION, is_superuser=True)
    assert can_delete_user(auth_gestion, user=boss, forbid_superuser=True) is False
    # en levant l’interdiction, on autorise
    assert can_delete_user(auth_gestion, user=boss, forbid_superuser=False) is True


def test_can_delete_user_without_target_allows_precheck(auth_gestion):
    # Lorsque user=None, la fonction retourne True si le rôle est GESTION,
    # laissant le service faire les vérifications (ex. chercher l’utilisateur).
    assert can_delete_user(auth_gestion, user=None) is True