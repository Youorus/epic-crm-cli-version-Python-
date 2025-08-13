from __future__ import annotations
import contextlib
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importe ta Base + ce que ton code utilise habituellement
from orm.models import Base  # ta MetaData avec tous les modèles
from services.db_session import session_scope as app_session_scope  # ton contextmanager applicatif
from services.db_session import engine as app_engine  # si tu en exposes un
from services.db_session import SessionLocal as AppSessionLocal

# ——————————————————————————————————————————
# 1) Engine en mémoire, partagé entre threads
# ——————————————————————————————————————————
@pytest.fixture(scope="session")
def memory_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # clé: une seule mémoire partagée
        future=True,
    )
    return engine

# ——————————————————————————————————————————
# 2) Base de données éphémère par session de tests
# ——————————————————————————————————————————
@pytest.fixture(scope="session", autouse=True)
def create_all(memory_engine):
    Base.metadata.create_all(memory_engine)
    yield
    Base.metadata.drop_all(memory_engine)

# ——————————————————————————————————————————
# 3) Session factory pour les tests
# ——————————————————————————————————————————
@pytest.fixture
def SessionTesting(memory_engine):
    return sessionmaker(bind=memory_engine, autoflush=False, autocommit=False, future=True)

# ——————————————————————————————————————————
# 4) Session transactionnelle par test
#    (rollback automatique après chaque test)
# ——————————————————————————————————————————
@pytest.fixture
def db(SessionTesting):
    # Connexion + transaction de niveau DB
    connection = SessionTesting.kw["bind"].connect()
    trans = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)

    try:
        session = TestingSessionLocal()
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()

# ——————————————————————————————————————————
# 5) Monkeypatch du session_scope() applicatif
#    pour qu’il utilise notre session de test
# ——————————————————————————————————————————
@pytest.fixture(autouse=True)
def patch_session_scope(monkeypatch, db):
    @contextlib.contextmanager
    def _test_session_scope():
        # Fournit la session de test existante (même transaction)
        yield db
        # Pas de commit/rollback ici: géré par la fixture db

    # Remplace le session_scope de l’app durant chaque test
    monkeypatch.setattr("services.db_session.session_scope", _test_session_scope)

# ——————————————————————————————————————————
# 6) Petites factories utiles (optionnel)
# ——————————————————————————————————————————
from enums.user_role import UserRole
from models.users import User
from models.clients import Client
from services.crud.user_repo import UserRepo
from services.crud.client_repo import ClientRepo

@pytest.fixture
def user_gestion(db):
    u = User.create(username="gestion", email="gestion@example.com", role=UserRole.GESTION, password="Azerty123$")
    return UserRepo(db).add(u)

@pytest.fixture
def user_commercial(db):
    u = User.create(username="comm", email="comm@example.com", role=UserRole.COMMERCIAL, password="Azerty123$")
    return UserRepo(db).add(u)

@pytest.fixture
def user_support(db):
    u = User.create(username="support", email="support@example.com", role=UserRole.SUPPORT, password="Azerty123$")
    return UserRepo(db).add(u)

@pytest.fixture
def client_for_comm(db, user_commercial):
    c = Client.create(
        full_name="Ada Lovelace",
        email="ada@example.com",
        phone="0612345678",
        company_name="Analytical Engines",
        sales_contact_id=user_commercial.id,
    )
    return ClientRepo(db).add(c)