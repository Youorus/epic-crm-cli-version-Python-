# cli/main.py
from __future__ import annotations

# 🔐 Login local (ton fichier)
from cli.auth.login import login, whoami
from cli.menu.menu_router import show_menu

# 🧭 Routeur des menus


# Optionnel : récupérer le rôle/username depuis le store JWT local
try:
    from security.session_state import get_auth
except Exception:
    get_auth = lambda: None  # fallback neutre


def main() -> None:
    """
    Lance la CLI :
    - Si l’utilisateur n’est pas connecté → invite à se connecter
    - Puis route vers le menu correspondant à son rôle
    """
    auth = get_auth()
    if not auth:
        # Pas de session → on demande une connexion
        rc = login()
        if rc != 0:
            return
        auth = get_auth()

    # Petit "whoami" sympa (facultatif)
    try:
        whoami()
    except Exception:
        pass

    # Redirige vers le bon menu
    show_menu()  # le routeur sait lire session.user OU get_auth()

if __name__ == "__main__":
    main()