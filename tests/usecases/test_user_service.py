# tests/services/test_user_service.py
from __future__ import annotations

import contextlib
import dataclasses
import pytest

from models.users import User
from security.authorization import AuthContext, AuthzError, Role
from services.usecases.user_crud import UserService


# ─────────────────────────────────────────────
# Doubles de test (pas de DB)
# ─────────────────────────────────────────────
@dataclasses.dataclass
class _Row:
    id: int
    email: str
    role: Role


class _FakeSession:
    pass


class _FakeUserRepo:
    _auto = 1

    def __init__(self, s, store: dict[int, _Row]):
        self.s = s
        self._store = store

    def add(self, u: User) -> User:
        uid = _FakeUserRepo._auto
        _FakeUserRepo._auto += 1
        u.id = uid
        self._store[uid] = _Row(id=uid, email=u.email, role=u.role)
        return u

    def get(self, user_id: int):
        r = self._store.get(user_id)
        if not r:
            return None
        # On reconstruit un User minimal (les validators s’appliquent)
        return User.create(username=f"user{r.id}", email=r.email, role=r.role)

    def list(self):
        for r in self._store.values():
            yield User.create(username=f"user{r.id}", email=r.email, role=r.role)

    def update(self, u: User) -> User:
        if u.id not in self._store:
            raise KeyError("not found")
        self._store[u.id] = _Row(id=u.id, email=u.email, role=u.role)
        return u

    def delete(self, user_id: int) -> None:
        self._store.pop(user_id, None)


@contextlib.contextmanager
def _fake_session_scope():
    yield _FakeSession()


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────
@pytest.fixture
def store() -> dict[int, _Row]:
    return {}


@pytest.fixture
def service(monkeypatch, store):
    import services.usecases.user_crud as uc
    # Remplace UserRepo et session_scope dans le module testé
    monkeypatch.setattr(uc, "UserRepo", lambda s: _FakeUserRepo(s, store))
    monkeypatch.setattr(uc, "session_scope", _fake_session_scope)
    return UserService()


@pytest.fixture
def auth_gestion() -> AuthContext:
    return AuthContext(user_id=1, role=Role.GESTION)


@pytest.fixture
def auth_support() -> AuthContext:
    return AuthContext(user_id=2, role=Role.SUPPORT)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def mk_user(email: str, role: Role = Role.SUPPORT) -> User:
    # username obligatoire côté modèle
    return User.create(username=email.split("@")[0], email=email, role=role, password="Azerty123$")


# ─────────────────────────────────────────────
# Tests: create
# ─────────────────────────────────────────────

# Tests: delete
# ─────────────────────────────────────────────