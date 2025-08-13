import types
import pytest

# Module sous test
import cli.services.users.update_user_form as mod

from enums.user_role import UserRole
from security.authorization import AuthContext, Role, AuthzError
from models.users import User


# --------------------------------------------------------------------------------------
# Fakes
# --------------------------------------------------------------------------------------
class FakeUserRepo:
    """
    Faux repo pour intercepter les accès à la DB dans update_user_form.
    Configure via attributs de classe :
      - by_id: dict[id] -> User (objet domaine)
      - usernames_taken: set[str]
      - emails_taken: set[str]
    """
    by_id = {}
    usernames_taken = set()
    emails_taken = set()

    def __init__(self, _s):
        pass

    def get_by_id(self, uid: int):
        return self.by_id.get(uid)

    # Ces deux méthodes sont appelées pour vérifier l’unicité
    def get_by_username(self, username: str):
        if username in self.usernames_taken:
            return types.SimpleNamespace(id=999, username=username)
        return None

    def get_by_email(self, email: str):
        if email in self.emails_taken:
            return types.SimpleNamespace(id=999, email=email)
        return None


class DummyServiceOK:
    """Service qui renvoie l’utilisateur modifié avec id (succès)."""
    def update(self, u: User, *, auth: AuthContext) -> User:
        u.id = (u.id or 1)
        return u


class DummyServiceReturnsNone:
    """Service qui simule 'introuvable' (update renvoie None)."""
    def update(self, u: User, *, auth: AuthContext):
        return None


class DummyServiceAuthzError:
    def update(self, u: User, *, auth: AuthContext):
        raise AuthzError("forbidden")


class DummyServiceCrash:
    def update(self, u: User, *, auth: AuthContext):
        raise RuntimeError("boom")


# --------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------
@pytest.fixture
def auth_gestion():
    return AuthContext(user_id=1, role=Role.GESTION)


@pytest.fixture(autouse=True)
def patch_session_and_repo(monkeypatch):
    """Patch session_scope et UserRepo pour tous les tests."""
    # session_scope no-op
    class _Ctx:
        def __enter__(self): return object()
        def __exit__(self, *exc): return False
    monkeypatch.setattr(mod, "session_scope", lambda: _Ctx(), raising=True)
    monkeypatch.setattr(mod, "UserRepo", FakeUserRepo, raising=True)


def _patch_inputs_for_confirm(monkeypatch, confirm="o"):
    """Patch builtins.input uniquement pour la confirmation finale."""
    it = iter([confirm])
    monkeypatch.setattr("builtins.input", lambda _p="": next(it))


def _patch_all_helpers(monkeypatch, *, new_username, new_email,
                       new_role=UserRole.SUPPORT,  # changement de rôle exemple
                       is_active=True, is_staff=False, is_superuser=False,
                       change_pwd=False):
    """
    Patch les helpers utilisés par le formulaire pour éviter l’IO interactive.
    - _input_int -> renvoie l’ID demandé
    - _prompt_keep_or_change -> renvoie la nouvelle valeur fournie
    - _validate_email -> no-op
    - _yes_no -> séquence pilotée (active, staff, superuser, change_pwd ?)
    - _choose_role -> renvoie le rôle demandé
    """
    # ID cible: 42
    monkeypatch.setattr(mod, "_input_int", lambda _prompt: 42, raising=True)

    seq_keep_or_change = iter([new_username, new_email])
    monkeypatch.setattr(
        mod,
        "_prompt_keep_or_change",
        lambda _label, _current: next(seq_keep_or_change),
        raising=True,
    )

    monkeypatch.setattr(mod, "_validate_email", lambda e: e, raising=True)
    monkeypatch.setattr(mod, "_choose_role", lambda current=None: new_role, raising=True)

    yn_answers = iter([is_active, is_staff, is_superuser, change_pwd])
    monkeypatch.setattr(mod, "_yes_no", lambda _q, default=None: next(yn_answers), raising=True)


# --------------------------------------------------------------------------------------
# Données de base (utilisateur existant)
# --------------------------------------------------------------------------------------
def _existing_user():
    return User(
        id=42,
        username="oldname",
        email="old@example.com",
        role=UserRole.GESTION,
        is_active=False,
        is_staff=False,
        is_superuser=False,
    )


# --------------------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------------------
def test_forbidden_role_returns_none(monkeypatch):
    """Un rôle non GESTION est refusé dès le début."""
    auth = AuthContext(user_id=2, role=Role.SUPPORT)
    FakeUserRepo.by_id = {42: _existing_user()}
    _patch_all_helpers(monkeypatch, new_username="x", new_email="y@example.com")
    _patch_inputs_for_confirm(monkeypatch, confirm="o")

    assert mod.update_user_form(service=DummyServiceOK(), auth=auth) is None


def test_user_not_found(monkeypatch, auth_gestion):
    """Si l’utilisateur n’existe pas, le formulaire échoue proprement."""
    FakeUserRepo.by_id = {}  # pas d’utilisateur 42
    _patch_all_helpers(monkeypatch, new_username="x", new_email="y@example.com")
    _patch_inputs_for_confirm(monkeypatch, confirm="o")

    assert mod.update_user_form(service=DummyServiceOK(), auth=auth_gestion) is None


def test_cancel_on_confirm(monkeypatch, auth_gestion):
    """Annulation sur la confirmation finale → None."""
    FakeUserRepo.by_id = {42: _existing_user()}
    _patch_all_helpers(monkeypatch, new_username="neo", new_email="neo@example.com")
    _patch_inputs_for_confirm(monkeypatch, confirm="n")

    assert mod.update_user_form(service=DummyServiceOK(), auth=auth_gestion) is None


def test_update_happy_path_change_fields_no_password(monkeypatch, auth_gestion):
    """Parcours heureux : on change username, email, rôle, flags — pas de mot de passe."""
    FakeUserRepo.by_id = {42: _existing_user()}
    FakeUserRepo.usernames_taken = set()
    FakeUserRepo.emails_taken = set()

    _patch_all_helpers(
        monkeypatch,
        new_username="newname",
        new_email="new@example.com",
        new_role=UserRole.SUPPORT,
        is_active=True,
        is_staff=True,
        is_superuser=False,
        change_pwd=False,
    )
    _patch_inputs_for_confirm(monkeypatch, confirm="o")

    updated = mod.update_user_form(service=DummyServiceOK(), auth=auth_gestion)
    assert updated is not None
    assert updated.id == 42
    assert updated.username == "newname"
    assert updated.email == "new@example.com"
    assert updated.role == UserRole.SUPPORT
    assert updated.is_active is True
    assert updated.is_staff is True
    assert updated.is_superuser is False


def test_update_with_password_change(monkeypatch, auth_gestion):
    """On change aussi le mot de passe (saisie 2x via getpass)."""
    FakeUserRepo.by_id = {42: _existing_user()}
    FakeUserRepo.usernames_taken = set()
    FakeUserRepo.emails_taken = set()

    _patch_all_helpers(
        monkeypatch,
        new_username="newname",
        new_email="new@example.com",
        new_role=UserRole.SUPPORT,
        is_active=True,
        is_staff=False,
        is_superuser=False,
        change_pwd=True,
    )
    # getpass patch (2 saisies identiques)
    it = iter(["StrongPass9!", "StrongPass9!"])
    monkeypatch.setattr(mod, "getpass", lambda _p="": next(it), raising=True)

    _patch_inputs_for_confirm(monkeypatch, confirm="o")

    updated = mod.update_user_form(service=DummyServiceOK(), auth=auth_gestion)
    assert updated is not None
    assert updated.username == "newname"
    # on ne vérifie pas le hash ici (c’est couvert ailleurs)


def test_duplicate_username(monkeypatch, auth_gestion):
    """Si le nouveau username est déjà pris (par un autre id), on bloque."""
    FakeUserRepo.by_id = {42: _existing_user()}
    FakeUserRepo.usernames_taken = {"taken"}
    FakeUserRepo.emails_taken = set()

    _patch_all_helpers(monkeypatch, new_username="taken", new_email="new@example.com")
    _patch_inputs_for_confirm(monkeypatch, confirm="o")

    assert mod.update_user_form(service=DummyServiceOK(), auth=auth_gestion) is None


def test_duplicate_email(monkeypatch, auth_gestion):
    """Si le nouvel email est déjà pris (par un autre id), on bloque."""
    FakeUserRepo.by_id = {42: _existing_user()}
    FakeUserRepo.usernames_taken = set()
    FakeUserRepo.emails_taken = {"dup@example.com"}

    _patch_all_helpers(monkeypatch, new_username="ok", new_email="dup@example.com")
    _patch_inputs_for_confirm(monkeypatch, confirm="o")

    assert mod.update_user_form(service=DummyServiceOK(), auth=auth_gestion) is None


def test_service_returns_none(monkeypatch, auth_gestion):
    """Le service renvoie None (introuvable/après vérifs) → None."""
    FakeUserRepo.by_id = {42: _existing_user()}
    _patch_all_helpers(monkeypatch, new_username="ok", new_email="ok@ex.com")
    _patch_inputs_for_confirm(monkeypatch, confirm="o")

    assert mod.update_user_form(service=DummyServiceReturnsNone(), auth=auth_gestion) is None


def test_service_authz_error(monkeypatch, auth_gestion):
    """Le service lève une AuthzError → None (message géré par le formulaire)."""
    FakeUserRepo.by_id = {42: _existing_user()}
    _patch_all_helpers(monkeypatch, new_username="ok", new_email="ok@ex.com")
    _patch_inputs_for_confirm(monkeypatch, confirm="o")

    assert mod.update_user_form(service=DummyServiceAuthzError(), auth=auth_gestion) is None


def test_service_unexpected_error(monkeypatch, auth_gestion):
    """Erreur inattendue pendant l’update → None (message d’erreur)."""
    FakeUserRepo.by_id = {42: _existing_user()}
    _patch_all_helpers(monkeypatch, new_username="ok", new_email="ok@ex.com")
    _patch_inputs_for_confirm(monkeypatch, confirm="o")

    assert mod.update_user_form(service=DummyServiceCrash(), auth=auth_gestion) is None