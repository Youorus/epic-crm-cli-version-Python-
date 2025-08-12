# fix_money_sqlite.py
# -*- coding: utf-8 -*-
from sqlalchemy import text
from services.db_session import engine

# 1) Supprimer € et TOUS les espaces (classiques, NBSP 160, NNBSP 8239)
SQL_STRIP = text("""
UPDATE contracts
SET
  total_amount = REPLACE(REPLACE(REPLACE(REPLACE(total_amount, '€',''), ' ', ''), CHAR(160), ''), CHAR(8239), ''),
  amount_due   = REPLACE(REPLACE(REPLACE(REPLACE(amount_due,   '€',''), ' ', ''), CHAR(160), ''), CHAR(8239), '');
""")

# 2) Transformer virgule en point
SQL_COMMA = text("""
UPDATE contracts
SET
  total_amount = REPLACE(total_amount, ',', '.'),
  amount_due   = REPLACE(amount_due,   ',', '.');
""")

# 3) CAST en REAL puis arrondi à 2 décimales
SQL_CAST = text("""
UPDATE contracts
SET
  total_amount = ROUND(CAST(total_amount AS REAL), 2),
  amount_due   = ROUND(CAST(amount_due   AS REAL), 2);
""")

if __name__ == "__main__":
    with engine.begin() as conn:
        conn.execute(SQL_STRIP)
        conn.execute(SQL_COMMA)
        conn.execute(SQL_CAST)
    print("✅ Montants normalisés dans la table contracts.")