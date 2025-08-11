# src/your_app/adapters/persistence/sqlalchemy/init_db.py
from sqlite.db import engine
from .models import Base

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Tables créées.")