# src/your_app/adapters/persistence/sqlalchemy/db.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

DB_URL = "sqlite:///data/app.db"
engine = create_engine(DB_URL, future=True)

# Activer les FK sur SQLite
@event.listens_for(engine, "connect")
def _fk_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)