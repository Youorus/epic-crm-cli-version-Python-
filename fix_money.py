# utils/fix_contracts_table.py
from __future__ import annotations
import os
import sqlite3
from urllib.parse import urlparse

# --- Résolution robuste du chemin DB ---
def _resolve_db_path() -> str:
    """
    Convertit DATABASE_URL (si présent) en chemin fichier SQLite.
    Accepte:
      - sqlite:///relative/path.db  (3 slashes)
      - sqlite:////abs/path.db      (4 slashes -> absolu)
      - /chemin/absolu/app.db       (déjà un chemin)
      - sinon fallback: <repo_root>/data/app.db
    """
    try:
        from utils.config import DATABASE_URL  # si tu as une config centralisée
    except Exception:
        DATABASE_URL = ""

    if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
        p = urlparse(DATABASE_URL)
        # p.path contient déjà le chemin absolu pour "sqlite:////abs/path.db"
        # et un chemin relatif pour "sqlite:///relative.db"
        path = p.path
        if os.name == "nt" and path.startswith("/"):  # Windows: /C:/...
            path = path.lstrip("/")
        if not os.path.isabs(path):
            # chemin relatif par rapport à la racine du repo
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            path = os.path.abspath(os.path.join(repo_root, path))
        return path

    # Si DATABASE_URL n'est pas une URL SQLite, on accepte un chemin brut
    if DATABASE_URL and (DATABASE_URL.endswith(".db") or os.sep in DATABASE_URL):
        return os.path.abspath(DATABASE_URL)

    # Fallback: <repo_root>/data/app.db
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(repo_root, "data", "app.db")


DB_PATH = _resolve_db_path()

DDL_CONTRACTS_NEW = """
CREATE TABLE IF NOT EXISTS contracts_new (
    id               INTEGER PRIMARY KEY,
    client_id        INTEGER NOT NULL,
    sales_contact_id INTEGER,
    total_amount     NUMERIC NOT NULL,
    amount_due       NUMERIC NOT NULL,
    is_signed        BOOLEAN NOT NULL DEFAULT 0,
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_contracts_total_amount_nonneg CHECK (total_amount >= 0),
    CONSTRAINT ck_contracts_amount_due_nonneg   CHECK (amount_due   >= 0)
);
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_contracts_sales_contact_id ON contracts_new (sales_contact_id);",
]

# Conversion texte -> NUMERIC (gère €, espaces, virgule, NULL)
COPY_SQL = """
INSERT INTO contracts_new (
    id, client_id, sales_contact_id, total_amount, amount_due, is_signed, created_at, updated_at
)
SELECT
    id,
    client_id,
    sales_contact_id,
    CASE
        WHEN total_amount IS NULL THEN 0
        ELSE CAST(REPLACE(REPLACE(REPLACE(total_amount, '€',''), ' ', ''), ',', '.') AS NUMERIC)
    END AS total_amount,
    CASE
        WHEN amount_due IS NULL THEN 0
        ELSE CAST(REPLACE(REPLACE(REPLACE(amount_due,   '€',''), ' ', ''), ',', '.') AS NUMERIC)
    END AS amount_due,
    CASE
        WHEN is_signed IN ('1','t','true','TRUE') THEN 1
        WHEN is_signed IN ('0','f','false','FALSE') THEN 0
        ELSE COALESCE(is_signed, 0)
    END AS is_signed,
    created_at,
    updated_at
FROM contracts;
"""

def main() -> None:
    # 1) S'assure que le dossier existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    print(f"[fix] Using DB: {DB_PATH}")

    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()
        cur.execute("PRAGMA foreign_keys = OFF;")

        # 2) Crée la nouvelle table avec bons types
        cur.execute(DDL_CONTRACTS_NEW)

        # 3) Copie depuis l'ancienne (si elle existe)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contracts';")
        if cur.fetchone():
            # Petit rapport de ce qui est encore texte (avant migration)
            try:
                cur.execute("""
                    SELECT id,
                           total_amount,
                           amount_due,
                           typeof(total_amount) AS ta_type,
                           typeof(amount_due)   AS ad_type
                    FROM contracts
                    WHERE typeof(total_amount) IN ('text','null')
                       OR typeof(amount_due)   IN ('text','null');
                """)
                rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]
                if rows:
                    print("⚠️  Lignes à convertir (avant migration) :")
                    for r in rows:
                        print(r)
            except Exception:
                pass

            cur.execute(COPY_SQL)
        else:
            print("ℹ️ Table 'contracts' introuvable : création d’une table vide.")

        # 4) Remplace l’ancienne table
        cur.execute("DROP TABLE IF EXISTS contracts;")
        cur.execute("ALTER TABLE contracts_new RENAME TO contracts;")

        # 5) Index
        for ddl in INDEXES:
            cur.execute(ddl)

        con.commit()
        print("✅ Table 'contracts' migrée → colonnes NUMERIC propres.")

        # 6) Vérification après migration (doit renvoyer 0 ligne)
        cur.execute("""
            SELECT id, total_amount, amount_due, typeof(total_amount) ta_type, typeof(amount_due) ad_type
            FROM contracts
            WHERE typeof(total_amount) != 'real' AND typeof(total_amount) != 'integer'
               OR typeof(amount_due)   != 'real' AND typeof(amount_due)   != 'integer';
        """)
        bad = cur.fetchall()
        if bad:
            print("⚠️  Des lignes non converties subsistent (attendu 0) :")
            cols = [c[0] for c in cur.description]
            for r in bad:
                print(dict(zip(cols, r)))
        else:
            print("🧪 Vérification OK : toutes les valeurs monétaires sont numériques.")
    finally:
        con.close()


if __name__ == "__main__":
    main()