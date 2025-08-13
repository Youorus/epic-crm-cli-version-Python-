# src/your_app/adapters/persistence/sqlite/init_db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/app.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")  # important pour FK
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Exemple minimal de tables (adapte à tes besoins)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        is_staff INTEGER NOT NULL DEFAULT 0,
        is_superuser INTEGER NOT NULL DEFAULT 0,
        last_login TEXT,
        date_joined TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        password_salt BLOB,
        password_hash BLOB
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT NOT NULL,
        company_name TEXT NOT NULL,
        last_contact TEXT,
        sales_contact_id INTEGER,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (sales_contact_id) REFERENCES user(id) ON DELETE SET NULL
    );
    """)

    cur.execute("""
   CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    sales_contact_id INTEGER,
    total_amount NUMERIC NOT NULL,  -- <- NUMERIC (affinité décimale)
    amount_due   NUMERIC NOT NULL,  -- <- NUMERIC
    is_signed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (sales_contact_id) REFERENCES user(id) ON DELETE SET NULL
);
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_id INTEGER NOT NULL UNIQUE,              -- OneToOne
        client_id INTEGER NOT NULL,
        support_contact_id INTEGER,
        event_name TEXT NOT NULL,
        event_start TEXT NOT NULL,
        event_end TEXT NOT NULL,
        location TEXT NOT NULL,
        attendees INTEGER NOT NULL,
        notes TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
        FOREIGN KEY (support_contact_id) REFERENCES user(id) ON DELETE SET NULL
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"SQLite initialisée à: {DB_PATH.resolve()}")