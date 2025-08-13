import types
import pytest

# Module à tester
import cli.services.users.create_user_form as mod

from enums.user_role import UserRole
from security.authorization import AuthContext, Role, AuthzError
from models.users import User


# --------------------------
# Fakes & helpers
# --------------------------

class FakeUserRepo:
    """
    Faux repo utilisé par create_user_form pour vérifier l'unicité.
    Configure via class attrs avant chaque test.
    """
    existing_usernames = set()
    existing_emails = set()

    def __init__(self, _session):
        pass

    def get_by_username(self, username):
        return types.SimpleNamespace(id=999) if username in self.existing_usernames else None

    def get_by_email(self, email):
        return types.SimpleNamespace(id=999) if email in self.existing_emails else None


class DummyServiceOK:
    """Service qui 'crée' et renvoie l'utilisateur avec un id."""
    def create(self, user: User, *, auth: AuthContext) -> User:
        user.id = 42
        return user


class DummyServiceAuthzError:
    def create(self, user: User, *, auth: AuthContext) -> User:
        raise AuthzError("nope")


# Fixture d’authentification (rôle GESTION par défaut)
@pytest.fixture
def auth_gestion():
    return AuthContext(user_id=1, role=Role.GESTION)


# Patch utilitaires du module
@pytest.fixture(autouse=True)
def patch_helpers(monkeypatch):
    # Evite la vraie validation email (qu’on teste ailleurs)
    monkeypatch.setattr(mod, "_validate_email", lambda e: e, raising=True)
    # Choix de rôle retourné par l’utilitaire (UserRole côté modèle)
    monkeypatch.setattr(mod, "_choose_role", lambda: UserRole.GESTION, raising=True)
    # Réponses aux questions oui/non
    answers = iter([True, False, False])  # is_active=True, is_staff=False, is_superuser=False
    monkeypatch.setattr(mod, "_yes_no", lambda _prompt, default=None: next(answers), raising=True)
    # S’assurer que _set_password_on_user ne fait rien de visible
    monkeypatch.setattr(mod, "_set_password_on_user", lambda u, pwd: None, raising=True)
    # Remplacer UserRepo par notre fake
    monkeypatch.setattr(mod, "UserRepo", FakeUserRepo, raising=True)
    # session_scope: contexte no-op
    class _Ctx:
        def __enter__(self): return object()
        def __exit__(self, *exc): return False
    monkeypatch.setattr(mod, "session_scope", lambda: _Ctx(), raising=True)


def _inputs(monkeypatch, seq):
    """Patch builtins.input pour renvoyer les valeurs de seq."""
    it = iter(seq)
    monkeypatch.setattr("builtins.input", lambda _p="": next(it))


def _getpass(monkeypatch, seq):
    """Patch mod.getpass (importé via 'from getpass import getpass')"""
    it = iter(seq)
    monkeypatch.setattr(mod, "getpass", lambda _p="": next(it), raising=True)


# --------------------------
# Tests
# --------------------------

def test_create_user_happy_path(monkeypatch, auth_gestion):
    """
    Parcours heureux : username/email uniques, rôle choisi, mot de passe OK,
    confirmation 'o' → retourne un User avec id.
    """
    FakeUserRepo.existing_usernames = set()
    FakeUserRepo.existing_emails = set()

    _inputs(monkeypatch, [
        "newuser",           # username
        "new@ex.com",        # email
        "o",                 # confirmer création
    ])
    _getpass(monkeypatch, [
        "Password123$",      # pwd1
        "Password123$",      # pwd2 (identique)
    ])

    created = mod.create_user_form(service=DummyServiceOK(), auth=auth_gestion)
    assert created is not None
    assert created.id == 42
    assert created.username == "newuser"
    assert created.email == "new@ex.com"
    assert created.role == UserRole.GESTION
    assert created.is_active is True
    assert created.is_staff is False
    assert created.is_superuser is False


def test_forbidden_role_returns_none(monkeypatch):
    """Un non-GESTION est refusé immédiatement."""
    auth = AuthContext(user_id=2, role=Role.SUPPORT)
    _inputs(monkeypatch, ["retour"])  # ne devrait pas être consommé, mais safe
    _getpass(monkeypatch, ["x", "x"])
    assert mod.create_user_form(service=DummyServiceOK(), auth=auth) is None


def test_duplicate_username_then_ok(monkeypatch, auth_gestion):
    """Premier username pris → on redemande, deuxième passe."""
    FakeUserRepo.existing_usernames = {"taken"}
    FakeUserRepo.existing_emails = set()

    _inputs(monkeypatch, [
        "taken",             # déjà pris
        "freeuser",          # ok
        "free@ex.com",       # email
        "o",                 # confirmer
    ])
    _getpass(monkeypatch, ["S3cret!ok", "S3cret!ok"])

    created = mod.create_user_form(service=DummyServiceOK(), auth=auth_gestion)
    assert created is not None
    assert created.username == "freeuser"


def test_duplicate_email_then_ok(monkeypatch, auth_gestion):
    """Premier email pris → on redemande, deuxième passe."""
    FakeUserRepo.existing_usernames = set()
    FakeUserRepo.existing_emails = {"dup@ex.com"}

    _inputs(monkeypatch, [
        "userok",            # username
        "dup@ex.com",        # déjà pris
        "unique@ex.com",     # ok
        "o",                 # confirmer
    ])
    _getpass(monkeypatch, ["S3cret!ok", "S3cret!ok"])

    created = mod.create_user_form(service=DummyServiceOK(), auth=auth_gestion)
    assert created is not None
    assert created.email == "unique@ex.com"


def test_cancel_on_retour_at_username(monkeypatch, auth_gestion):
    """Saisie 'retour' au username annule le formulaire."""
    _inputs(monkeypatch, ["retour"])
    _getpass(monkeypatch, ["x", "x"])
    assert mod.create_user_form(service=DummyServiceOK(), auth=auth_gestion) is None


def test_invalid_email_then_valid(monkeypatch, auth_gestion):
    """_validate_email lève d’abord, puis passe."""
    calls = {"n": 0}
    def _valid(e):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValueError("email invalide")
        return e
    # override le patch par défaut
    monkeypatch.setattr(mod, "_validate_email", _valid, raising=True)

    _inputs(monkeypatch, [
        "userok",            # username
        "bad",               # invalide → repeat
        "good@ex.com",       # ok
        "o",                 # confirmer
    ])
    _getpass(monkeypatch, ["S3cret!ok", "S3cret!ok"])

    created = mod.create_user_form(service=DummyServiceOK(), auth=auth_gestion)
    assert created is not None
    assert created.email == "good@ex.com"




def test_cancel_on_confirm(monkeypatch, auth_gestion):
    """Refus sur la confirmation finale → None."""
    _inputs(monkeypatch, [
        "userok",
        "mail@ex.com",
        "n",                 # ne pas confirmer
    ])
    _getpass(monkeypatch, ["TopSecret9!", "TopSecret9!"])
    assert mod.create_user_form(service=DummyServiceOK(), auth=auth_gestion) is None


def test_authz_error_from_service(monkeypatch, auth_gestion):
    """Le service lève AuthzError → None."""
    _inputs(monkeypatch, [
        "userok",
        "mail@ex.com",
        "o",
    ])
    _getpass(monkeypatch, ["TopSecret9!", "TopSecret9!"])
    assert mod.create_user_form(service=DummyServiceAuthzError(), auth=auth_gestion) is None