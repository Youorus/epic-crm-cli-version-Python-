# tests/services/test_event_service.py
from __future__ import annotations

import contextlib
import dataclasses
from datetime import datetime, timedelta, timezone
import pytest

from models.event import Event
from models.contract import Contract
from security.authorization import AuthContext, Role, AuthzError
from services.usecases.event_crud import EventService


# ─────────────────────────────────────────────────────────
# Doubles / fakes
# ─────────────────────────────────────────────────────────
UTC = timezone.utc
now = datetime.now(UTC)

@dataclasses.dataclass
class _ContractRow:
    id: int
    client_id: int
    sales_contact_id: int | None
    is_signed: bool

@dataclasses.dataclass
class _EventRow:
    id: int | None
    contract_id: int
    client_id: int
    support_contact_id: int | None
    event_name: str
    event_start: datetime
    event_end: datetime
    location: str
    attendees: int
    notes: str


class FakeSession:
    pass


class FakeContractRepo:
    def __init__(self, s, store: dict[int, _ContractRow]):
        self.s = s
        self._store = store

    def get(self, contract_id: int | None):
        if not contract_id:
            return None
        row = self._store.get(int(contract_id))
        if not row:
            return None
        # On retourne une entité Contract minimale (seulement champs utilisés par l’auth)
        return Contract(
            id=row.id,
            client_id=row.client_id,
            sales_contact_id=row.sales_contact_id,
            total_amount="0.00",
            amount_due="0.00",
            is_signed=row.is_signed,
        )


class FakeEventRepo:
    _auto = 1

    def __init__(self, s, store: dict[int, _EventRow]):
        self.s = s
        self._store = store

    def add(self, e: Event) -> Event:
        eid = FakeEventRepo._auto
        FakeEventRepo._auto += 1
        e.id = eid
        self._store[eid] = _EventRow(
            id=eid,
            contract_id=e.contract_id,
            client_id=e.client_id,
            support_contact_id=e.support_contact_id,
            event_name=e.event_name,
            event_start=e.event_start,
            event_end=e.event_end,
            location=e.location,
            attendees=e.attendees,
            notes=e.notes or "",
        )
        return e

    def get(self, event_id: int | None) -> Event | None:
        if not event_id:
            return None
        r = self._store.get(int(event_id))
        if not r:
            return None
        return Event(
            id=r.id,
            contract_id=r.contract_id,
            client_id=r.client_id,
            support_contact_id=r.support_contact_id,
            event_name=r.event_name,
            event_start=r.event_start,
            event_end=r.event_end,
            location=r.location,
            attendees=r.attendees,
            notes=r.notes,
        )

    def list(self):
        for r in list(self._store.values()):
            yield Event(
                id=r.id,
                contract_id=r.contract_id,
                client_id=r.client_id,
                support_contact_id=r.support_contact_id,
                event_name=r.event_name,
                event_start=r.event_start,
                event_end=r.event_end,
                location=r.location,
                attendees=r.attendees,
                notes=r.notes,
            )

    def update(self, e: Event) -> Event:
        assert e.id is not None
        if e.id not in self._store:
            raise KeyError("not found")
        self._store[e.id] = _EventRow(
            id=e.id,
            contract_id=e.contract_id,
            client_id=e.client_id,
            support_contact_id=e.support_contact_id,
            event_name=e.event_name,
            event_start=e.event_start,
            event_end=e.event_end,
            location=e.location,
            attendees=e.attendees,
            notes=e.notes or "",
        )
        return e

    def delete(self, event_id: int) -> None:
        self._store.pop(int(event_id), None)


@contextlib.contextmanager
def fake_session_scope():
    yield FakeSession()


# ─────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────
@pytest.fixture
def contracts_store() -> dict[int, _ContractRow]:
    return {}


@pytest.fixture
def events_store() -> dict[int, _EventRow]:
    return {}


@pytest.fixture
def service(monkeypatch, contracts_store, events_store) -> EventService:
    import services.usecases.event_crud as uc
    # Patch des repos + session_scope
    monkeypatch.setattr(uc, "ContractRepo", lambda s: FakeContractRepo(s, contracts_store))
    monkeypatch.setattr(uc, "EventRepo",    lambda s: FakeEventRepo(s, events_store))
    monkeypatch.setattr(uc, "session_scope", fake_session_scope)
    return EventService()


@pytest.fixture
def auth_gestion() -> AuthContext:
    return AuthContext(user_id=1, role=Role.GESTION)

@pytest.fixture
def auth_commercial() -> AuthContext:
    return AuthContext(user_id=2, role=Role.COMMERCIAL)

@pytest.fixture
def auth_support() -> AuthContext:
    return AuthContext(user_id=3, role=Role.SUPPORT)

@pytest.fixture
def signed_contract(contracts_store, auth_commercial) -> _ContractRow:
    row = _ContractRow(id=10, client_id=101, sales_contact_id=auth_commercial.user_id, is_signed=True)
    contracts_store[row.id] = row
    return row

@pytest.fixture
def unsigned_contract(contracts_store, auth_commercial) -> _ContractRow:
    row = _ContractRow(id=11, client_id=102, sales_contact_id=auth_commercial.user_id, is_signed=False)
    contracts_store[row.id] = row
    return row


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
def _mk_event(contract_id: int, client_id: int, support_id: int | None = None, *, name="Kickoff") -> Event:
    return Event.create(
        contract_id=contract_id,
        client_id=client_id,
        event_name=name,
        event_start=now + timedelta(hours=1),
        event_end=now + timedelta(hours=2),
        location="HQ",
        attendees=5,
        support_contact_id=support_id,
        notes="",
    )


# ─────────────────────────────────────────────────────────
# Tests : create
# ─────────────────────────────────────────────────────────
def test_create_gestion_ok(service: EventService, auth_gestion, signed_contract):
    e = _mk_event(signed_contract.id, signed_contract.client_id)
    created = service.create(e, auth=auth_gestion)
    assert created.id is not None

def test_create_commercial_only_if_owner_and_signed(service: EventService, auth_commercial, signed_contract, unsigned_contract):
    # OK : commercial propriétaire et contrat signé
    e = _mk_event(signed_contract.id, signed_contract.client_id)
    created = service.create(e, auth=auth_commercial)
    assert created.id is not None

    # KO : commercial propriétaire mais contrat non signé
    e2 = _mk_event(unsigned_contract.id, unsigned_contract.client_id)
    with pytest.raises(AuthzError):
        service.create(e2, auth=auth_commercial)

def test_create_raises_if_contract_not_found(service: EventService, auth_gestion):
    e = _mk_event(9999, 7777)
    with pytest.raises(ValueError):
        service.create(e, auth=auth_gestion)


# ─────────────────────────────────────────────────────────
# Tests : get / list (lecture autorisée à tous)
# ─────────────────────────────────────────────────────────
def test_get_and_list(service: EventService, auth_gestion, auth_support, signed_contract):
    # seed: un event
    created = service.create(_mk_event(signed_contract.id, signed_contract.client_id, support_id=42), auth=auth_gestion)

    # get
    assert service.get(created.id, auth=auth_support).id == created.id  # support peut lire

    # list: GESTION voit tout
    all_evts = service.list(auth=auth_gestion)
    assert {e.id for e in all_evts} == {created.id}

def test_list_filtering_by_role_support(service: EventService, auth_gestion, auth_support, signed_contract, events_store, monkeypatch):
    # Deux événements : un assigné au support (id=3), un sans support
    e1 = service.create(_mk_event(signed_contract.id, signed_contract.client_id, support_id=auth_support.user_id, name="Mine"), auth=auth_gestion)
    e2 = service.create(_mk_event(signed_contract.id, signed_contract.client_id, support_id=None, name="Other"), auth=auth_gestion)

    # La fonction filter_events_for est appelée dans le service.list()
    # Par défaut (implémentation actuelle) : SUPPORT ne voit que ceux qui lui sont assignés.
    mine = service.list(auth=auth_support)
    assert {e.id for e in mine} == {e1.id}


# ─────────────────────────────────────────────────────────
# Tests : update
# ─────────────────────────────────────────────────────────
def test_update_allowed_for_gestion(service: EventService, auth_gestion, signed_contract):
    e = service.create(_mk_event(signed_contract.id, signed_contract.client_id, support_id=None), auth=auth_gestion)
    e.notes = "new"
    assert service.update(e, auth=auth_gestion).notes == "new"

def test_update_allowed_for_assigned_support(service: EventService, auth_gestion, auth_support, signed_contract):
    e = service.create(_mk_event(signed_contract.id, signed_contract.client_id, support_id=auth_support.user_id), auth=auth_gestion)
    e.location = "Field"
    assert service.update(e, auth=auth_support).location == "Field"

def test_update_forbidden_for_other_support(service: EventService, auth_gestion, signed_contract):
    # event assigné à support_id=99
    e = service.create(_mk_event(signed_contract.id, signed_contract.client_id, support_id=99), auth=auth_gestion)
    with pytest.raises(AuthzError):
        service.update(e, auth=AuthContext(user_id=3, role=Role.SUPPORT))


# ─────────────────────────────────────────────────────────
# Tests : delete
# ─────────────────────────────────────────────────────────
def test_delete_only_gestion(service: EventService, auth_gestion, auth_support, signed_contract):
    e = service.create(_mk_event(signed_contract.id, signed_contract.client_id), auth=auth_gestion)

    with pytest.raises(AuthzError):
        service.delete(e.id, auth=auth_support)

    service.delete(e.id, auth=auth_gestion)
    assert service.get(e.id, auth=auth_gestion) is None


# ─────────────────────────────────────────────────────────
# Tests : assign_support (GESTION only)
# ─────────────────────────────────────────────────────────
def test_assign_support_only_gestion(service: EventService, auth_gestion, auth_support, signed_contract):
    e = service.create(_mk_event(signed_contract.id, signed_contract.client_id, support_id=None), auth=auth_gestion)

    # KO si support tente d'assigner
    with pytest.raises(AuthzError):
        service.assign_support(event_id=e.id, support_user_id=auth_support.user_id, auth=auth_support)

    # OK pour gestion
    updated = service.assign_support(event_id=e.id, support_user_id=auth_support.user_id, auth=auth_gestion)
    assert updated and updated.support_contact_id == auth_support.user_id