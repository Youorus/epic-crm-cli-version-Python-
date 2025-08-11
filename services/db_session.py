# services/db_session.py
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from utils.config import DATABASE_URL

# Création de l'engine SQLAlchemy
# echo=True pour debug SQL, à désactiver en prod
engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True  # vérifie que la connexion est toujours vivante
)

# Fabrique de sessions
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)

@contextmanager
def session_scope():
    """
    Fournit un contexte transactionnel pour les opérations sur la DB.

    Usage :
        with session_scope() as session:
            session.add(obj)
            ...
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()