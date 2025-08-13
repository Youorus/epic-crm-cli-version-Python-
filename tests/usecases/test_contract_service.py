# tests/services/test_contract_service.py
from __future__ import annotations

import contextlib
import dataclasses
from decimal import Decimal
import pytest

from models.contract import Contract
from security.authorization import AuthContext, Role, AuthzError
from services.usecases.client_crud import ClientService  # juste pour type import si besoin
from services.usecases.contract_crud import ContractService


# ─────────────────────────────────────────────────────────
# Doubles / fakes
# ─────────────────────────────────────────────────────────
class FakeSession:
    pass


@dataclasses.dataclass
class _Row:
    id: int | None
    client_id: int
    sales_contact_id: int | None
    total_amount: Decimal
    amount_due: Decimal
    is_signed: bool


class FakeContractRepo:
    """Repo en mémoire, API compatible avec ContractRepo."""
    _auto = 1

    def __init__(self, s, store: dict[int, _Row]):
        self.s = s
        self._store = store

    def add(self, c: Contract) -> Contract:
        cid = FakeContractRepo._auto
        FakeContractRepo._auto += 1
        c.id = cid
        self._store[cid] = _Row(
            id=cid,
            client_id=c.client_id,
            sales_contact_id=c.sales_contact_id,
            total_amount=c.total_amount,
            amount_due=c.amount_due,
            is_signed=c.is_signed,
        )
        return c

    def get(self, contract_id: int | None) -> Contract | None:
        if not contract_id:
            return None
        r = self._store.get(int(contract_id))
        if not r:
            return None
        return Contract(
            id=r.id,
            client_id=r.client_id,
            sales_contact_id=r.sales_contact_id,
            total_amount=r.total_amount,
            amount_due=r.amount_due,
            is_signed=r.is_signed,
        )

    def list(self):
        for r in list(self._store.values()):
            yield Contract(
                id=r.id,
                client_id=r.client_id,
                sales_contact_id=r.sales_contact_id,
                total_amount=r.total_amount,
                amount_due=r.amount_due,
                is_signed=r.is_signed,
            )

    def update(self, c: Contract) -> Contract:
        assert c.id is not None
        if c.id not in self._store:
            raise KeyError("not found")
        self._store[c.id] = _Row(
            id=c.id,
            client_id=c.client_id,
            sales_contact_id=c.sales_contact_id,
            total_amount=c.total_amount,
            amount_due=c.amount_due,
            is_signed=c.is_signed,
        )
        return c

    def delete(self, contract_id: int) -> None:
        self._store.pop(int(contract_id), None)


@contextlib.contextmanager
def fake_session_scope():
    yield FakeSession()


# ─────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────
@pytest.fixture
def store() -> dict[int, _Row]:
    return {}


@pytest.fixture
def service(monkeypatch, store) -> ContractService:
    import services.usecases.contract_crud as uc

    # Branche les doubles
    monkeypatch.setattr(uc, "ContractRepo", lambda s: FakeContractRepo(s, store))
    monkeypatch.setattr(uc, "session_scope", fake_session_scope)

    return ContractService()


@pytest.fixture
def auth_gestion() -> AuthContext:
    return AuthContext(user_id=1, role=Role.GESTION)


@pytest.fixture
def auth_commercial() -> AuthContext:
    return AuthContext(user_id=2, role=Role.COMMERCIAL)


@pytest.fixture
def auth_other_com() -> AuthContext:
    return AuthContext(user_id=3, role=Role.COMMERCIAL)


@pytest.fixture
def auth_support() -> AuthContext:
    return AuthContext(user_id=4, role=Role.SUPPORT)


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
def _make_contract(
    *,
    client_id: int,
    sales_contact_id: int | None,
    total: str = "1000.00",
    due: str = "1000.00",
    signed: bool = False,
) -> Contract:
    return Contract.create(
        client_id=client_id,
        sales_contact_id=sales_contact_id,
        total_amount=Decimal(total),
        amount_due=Decimal(due),
        is_signed=signed,
    )


# ─────────────────────────────────────────────────────────
# Tests : create
# ─────────────────────────────────────────────────────────
def test_create_allowed_only_for_gestion(service: ContractService, auth_gestion, auth_commercial, auth_support):
    c = _make_contract(client_id=10, sales_contact_id=auth_commercial.user_id)
    created = service.create(c, auth=auth_gestion)
    assert created.id is not None

    with pytest.raises(AuthzError):
        service.create(_make_contract(client_id=11, sales_contact_id=auth_commercial.user_id), auth=auth_commercial)

    with pytest.raises(AuthzError):
        service.create(_make_contract(client_id=12, sales_contact_id=None), auth=auth_support)


# ─────────────────────────────────────────────────────────
# Tests : get / list (filtrage)
# ─────────────────────────────────────────────────────────
def test_get_requires_read_rights(service: ContractService, auth_gestion, auth_support):
    created = service.create(_make_contract(client_id=1, sales_contact_id=None), auth=auth_gestion)
    got = service.get(created.id, auth=auth_support)  # lecture autorisée à tous les rôles (cahier des charges)
    assert got and got.id == created.id



# ─────────────────────────────────────────────────────────
# Tests : update
# ─────────────────────────────────────────────────────────
def test_update_allowed_for_gestion(service: ContractService, auth_gestion):
    c = service.create(_make_contract(client_id=1, sales_contact_id=None, total="1000.00", due="400.00"), auth=auth_gestion)
    c.amount_due = Decimal("200.00")
    updated = service.update(c, auth=auth_gestion)
    assert updated and updated.amount_due == Decimal("200.00")


def test_update_allowed_for_owner_commercial(service: ContractService, auth_gestion, auth_commercial):
    c = service.create(_make_contract(client_id=1, sales_contact_id=auth_commercial.user_id, total="1000.00", due="700.00"), auth=auth_gestion)
    c.amount_due = Decimal("500.00")
    updated = service.update(c, auth=auth_commercial)
    assert updated and updated.amount_due == Decimal("500.00")


def test_update_forbidden_for_other_commercial(service: ContractService, auth_gestion, auth_commercial, auth_other_com):
    c = service.create(_make_contract(client_id=1, sales_contact_id=auth_commercial.user_id), auth=auth_gestion)
    c.is_signed = True
    with pytest.raises(AuthzError):
        service.update(c, auth=auth_other_com)


# ─────────────────────────────────────────────────────────
# Tests : delete
# ─────────────────────────────────────────────────────────
def test_delete_allowed_only_for_gestion(service: ContractService, auth_gestion, auth_commercial):
    c = service.create(_make_contract(client_id=1, sales_contact_id=auth_commercial.user_id), auth=auth_gestion)

    with pytest.raises(AuthzError):
        service.delete(c.id, auth=auth_commercial)

    # GESTION peut supprimer
    service.delete(c.id, auth=auth_gestion)
    assert service.get(c.id, auth=auth_gestion) is None