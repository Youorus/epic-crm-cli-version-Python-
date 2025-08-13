# tests/services/test_client_service.py
from __future__ import annotations

import contextlib
import dataclasses
import pytest

from models.clients import Client
from security.authorization import AuthContext, Role, AuthzError
from services.usecases.client_crud import ClientService


# ─────────────────────────────────────────────────────────
# Doubles / fakes
# ─────────────────────────────────────────────────────────
@dataclasses.dataclass
class FakeOrmClient:
    """Représente un enregistrement 'ORM' minimal pour le FakeRepo (pas utilisé directement par le service)."""
    id: int | None
    full_name: str
    email: str
    phone: str
    company_name: str
    last_contact: object | None = None
    sales_contact_id: int | None = None


class FakeClientRepo:
    """Repo en mémoire avec l'API attendue par ClientService."""
    _auto_id = 1

    def __init__(self, _session, store: dict[int, Client]):
        self.s = _session
        self._store = store

    # API attendue par le service
    def add(self, client: Client) -> Client:
        cid = FakeClientRepo._auto_id
        FakeClientRepo._auto_id += 1
        client.id = cid
        # on clone pour simuler une vraie persistance
        self._store[cid] = Client(
            id=client.id,
            full_name=client.full_name,
            email=client.email,
            phone=client.phone,
            company_name=client.company_name,
            last_contact=client.last_contact,
            sales_contact_id=client.sales_contact_id,
        )
        return client

    def get(self, client_id: int | None) -> Client | None:
        if client_id is None:
            return None
        c = self._store.get(int(client_id))
        if not c:
            return None
        # retourner une copie pour éviter mutation partagée
        return Client(
            id=c.id,
            full_name=c.full_name,
            email=c.email,
            phone=c.phone,
            company_name=c.company_name,
            last_contact=c.last_contact,
            sales_contact_id=c.sales_contact_id,
        )

    def list(self):
        # itérateur de Clients (copies)
        for c in list(self._store.values()):
            yield Client(
                id=c.id,
                full_name=c.full_name,
                email=c.email,
                phone=c.phone,
                company_name=c.company_name,
                last_contact=c.last_contact,
                sales_contact_id=c.sales_contact_id,
            )

    def update(self, client: Client) -> Client:
        assert client.id is not None, "update() requiert un id"
        if client.id not in self._store:
            raise KeyError("not found")
        # remplace la valeur
        self._store[client.id] = Client(
            id=client.id,
            full_name=client.full_name,
            email=client.email,
            phone=client.phone,
            company_name=client.company_name,
            last_contact=client.last_contact,
            sales_contact_id=client.sales_contact_id,
        )
        return client

    def delete(self, client_id: int) -> None:
        self._store.pop(int(client_id), None)


@contextlib.contextmanager
def fake_session_scope():
    """Remplace services.db_session.session_scope; ne fait rien mais respecte l’API."""
    yield object()


# ─────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────
@pytest.fixture
def store() -> dict[int, Client]:
    """Magasin en mémoire isolé par test."""
    return {}


@pytest.fixture
def service(monkeypatch, store) -> ClientService:
    """
    Branche les doubles :
      - services.usecases.client_crud.ClientRepo -> FakeClientRepo
      - services.usecases.client_crud.session_scope -> fake_session_scope
    """
    import services.usecases.client_crud as uc

    monkeypatch.setattr(uc, "ClientRepo", lambda s: FakeClientRepo(s, store))
    monkeypatch.setattr(uc, "session_scope", fake_session_scope)

    return ClientService()


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
# Tests : create
# ─────────────────────────────────────────────────────────
def test_create_allowed_for_gestion(service: ClientService, auth_gestion):
    c = Client.create(
        full_name="Ada Lovelace",
        email="ada@example.com",
        phone="+33123456789",
        company_name="Analytical Engines",
    )
    created = service.create(c, auth=auth_gestion)
    assert created.id is not None
    assert created.sales_contact_id is None  # pas d’auto-assignation pour GESTION


def test_create_allowed_for_commercial_auto_assign(service: ClientService, auth_commercial):
    c = Client.create(
        full_name="Alan Turing",
        email="alan@example.com",
        phone="+441234567890",
        company_name="Enigma Ltd",
    )
    created = service.create(c, auth=auth_commercial)
    assert created.id is not None
    # Auto-assignation au commercial connecté si non fourni
    assert created.sales_contact_id == auth_commercial.user_id


def test_create_forbidden_for_support(service: ClientService, auth_support):
    c = Client.create(
        full_name="Grace Hopper",
        email="grace@example.com",
        phone="+33612345678",
        company_name="COBOL Inc.",
    )
    with pytest.raises(AuthzError):
        service.create(c, auth=auth_support)


# ─────────────────────────────────────────────────────────
# Tests : get / list (avec filtrage)
# ─────────────────────────────────────────────────────────
def _seed_three_clients(service: ClientService, auth_gestion, owner_id: int):
    """Utilitaire : 3 clients, dont 2 assignés au COMMERCIAL owner_id."""
    c1 = Client.create(full_name="C1", email="c1@example.com", phone="1", company_name="X", sales_contact_id=owner_id)
    c2 = Client.create(full_name="C2", email="c2@example.com", phone="2", company_name="Y", sales_contact_id=owner_id)
    c3 = Client.create(full_name="C3", email="c3@example.com", phone="3", company_name="Z", sales_contact_id=None)
    a = service.create(c1, auth=auth_gestion)
    b = service.create(c2, auth=auth_gestion)
    d = service.create(c3, auth=auth_gestion)
    return a, b, d


def test_get_requires_read_rights(service: ClientService, auth_support):
    c = service.create(
        Client.create(full_name="X", email="x@example.com", phone="1", company_name="Acme"),
        auth=AuthContext(1, Role.GESTION),
    )
    got = service.get(c.id, auth=auth_support)
    assert got and got.id == c.id


def test_list_filters_for_commercial(service: ClientService, auth_gestion, auth_commercial):
    a, b, d = _seed_three_clients(service, auth_gestion, owner_id=auth_commercial.user_id)

    # GESTION voit tout
    all_for_gestion = service.list(auth=auth_gestion)
    assert {c.id for c in all_for_gestion} == {a.id, b.id, d.id}

    # COMMERCIAL ne voit que ses clients (a, b)
    only_mine = service.list(auth=auth_commercial)
    assert {c.id for c in only_mine} == {a.id, b.id}


# ─────────────────────────────────────────────────────────
# Tests : update
# ─────────────────────────────────────────────────────────
def test_update_allowed_for_gestion(service: ClientService, auth_gestion):
    c = service.create(
        Client.create(full_name="Up", email="up@example.com", phone="1", company_name="Acme"),
        auth=auth_gestion,
    )
    c.company_name = "NewCo"
    updated = service.update(c, auth=auth_gestion)
    assert updated and updated.company_name == "NewCo"


def test_update_allowed_for_owner_commercial(service: ClientService, auth_gestion, auth_commercial):
    c = service.create(
        Client.create(full_name="Mine", email="mine@example.com", phone="1", company_name="AC", sales_contact_id=auth_commercial.user_id),
        auth=auth_gestion,
    )
    c.company_name = "MyCo"
    updated = service.update(c, auth=auth_commercial)
    assert updated and updated.company_name == "MyCo"


def test_update_forbidden_for_other_commercial(service: ClientService, auth_gestion):
    owner = AuthContext(7, Role.COMMERCIAL)
    other = AuthContext(8, Role.COMMERCIAL)

    c = service.create(
        Client.create(full_name="Owned", email="owned@example.com", phone="1", company_name="AC", sales_contact_id=owner.user_id),
        auth=auth_gestion,
    )
    c.company_name = "HackCo"
    with pytest.raises(AuthzError):
        service.update(c, auth=other)


# ─────────────────────────────────────────────────────────
# Tests : delete
# ─────────────────────────────────────────────────────────
def test_delete_allowed_for_gestion(service: ClientService, auth_gestion):
    c = service.create(
        Client.create(full_name="Del", email="del@example.com", phone="1", company_name="AC"),
        auth=auth_gestion,
    )
    service.delete(c.id, auth=auth_gestion)
    assert service.get(c.id, auth=auth_gestion) is None


def test_delete_forbidden_for_commercial(service: ClientService, auth_gestion, auth_commercial):
    c = service.create(
        Client.create(full_name="NoDel", email="nodel@example.com", phone="1", company_name="AC"),
        auth=auth_gestion,
    )
    with pytest.raises(AuthzError):
        service.delete(c.id, auth=auth_commercial)