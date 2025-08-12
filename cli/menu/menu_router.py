# cli/menus/menu_router.py
from __future__ import annotations

from cli.menu.commercial_menu import commercial_menu
from cli.menu.gestion_menu import gestion_menu
from cli.menu.support_menu import support_menu
from cli.menu.utils import _current_role, _current_username

def show_menu() -> None:
    """
    Routeur principal des menus CLI selon le rôle de l'utilisateur connecté.

    🔹 Lit d’abord session.user (variante API),
       sinon lit security.session_state.get_auth() (variante locale).
    🔹 Redirige vers :
        - GESTION     → gestion_menu()
        - COMMERCIAL  → commercial_menu()
        - SUPPORT     → support_menu()
    """
    role = _current_role()
    username = _current_username()

    if not role:
        print("❌ Aucun utilisateur connecté. Veuillez vous authentifier.")
        return


    if username:
        print(f"👋 Bonjour {username} ({role})")


    if role == "GESTION":
        gestion_menu()
    elif role == "COMMERCIAL":
        commercial_menu()
    elif role == "SUPPORT":
        support_menu()
    else:
        print(f"❌ Rôle non reconnu ou non autorisé : {role}")