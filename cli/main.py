from __future__ import annotations
from utils.sentry_init import init_sentry

# Initialiser Sentry avant tout
init_sentry()

from cli.auth.login import login, whoami
from cli.menu.menu_router import show_menu

try:
    from security.auth_session import get_auth
except Exception:
    get_auth = lambda: None

def main() -> None:
    """Point d’entrée de la CLI."""
    auth = get_auth()
    if not auth:
        rc = login()
        if rc != 0:
            return

    try:
        whoami()
    except Exception:
        pass

    show_menu()

if __name__ == "__main__":
    main()