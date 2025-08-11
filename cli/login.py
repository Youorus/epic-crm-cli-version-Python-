# cli/login.py
from __future__ import annotations
import getpass

from services.crud.user_repo import UserRepo
from security.passwords import verify_password
from security.jwt import create_access_token, create_refresh_token
from security.session_state import save_tokens, clear_token, get_auth
from services.db_session import session_scope, engine
import os, services.db_session as dbs

def login() -> int:
    print("\n=== Connexion Epic Events (local) ===")
    ident = input("Email ou username: ").strip()
    password = getpass.getpass("Mot de passe: ")

    with session_scope() as s:
        repo = UserRepo(s)
        orm = repo.get_by_email_or_username(ident)
        if not orm:
            print("❌ Identifiants invalides.")
            return 1

        if not orm.password_salt or not orm.password_hash:
            print("❌ Utilisateur sans mot de passe défini.")
            return 1

        if not verify_password(password, orm.password_salt, orm.password_hash):
            print("❌ Identifiants invalides.")
            return 1

        access = create_access_token(user_id=orm.id, role=str(orm.role))
        refresh = create_refresh_token(user_id=orm.id, role=str(orm.role))

        save_tokens(access, refresh)
        print(f"✅ Connecté en tant que {orm.username} ({orm.role}).")
        return 0


def logout() -> int:
    clear_token()
    print("👋 Déconnecté.")
    return 0


def whoami() -> int:
    auth = get_auth()
    if not auth:
        print("❌ Aucune session active.")
        return 1
    print(f"👤 Session active — user_id={auth.user_id}, role={auth.role}")
    return 0


if __name__ == "__main__":
    import sys
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "login").lower()
    if cmd == "login":
        raise SystemExit(login())
    if cmd == "logout":
        raise SystemExit(logout())
    if cmd == "whoami":
        raise SystemExit(whoami())
    print("Usage: python -m cli.login [login|logout|whoami]")
    raise SystemExit(2)