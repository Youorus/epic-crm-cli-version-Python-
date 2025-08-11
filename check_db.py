# scripts/check_db.py
from sqlalchemy import text, inspect

from orm.db import engine, SessionLocal


def main():
    # Test engine direct
    with engine.connect() as conn:
        version = conn.execute(text("SELECT sqlite_version();")).scalar_one()
        print(f"✅ Connexion OK - SQLite {version}")

    # Test session ORM
    with SessionLocal() as s:
        s.execute(text("SELECT 1"))
        print("✅ Session ORM OK")

    # Lister les tables
    insp = inspect(engine)
    print("📦 Tables:", ", ".join(sorted(insp.get_table_names())) or "(aucune)")

if __name__ == "__main__":
    main()