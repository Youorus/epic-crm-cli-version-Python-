# cli/menus/support_menu.py
from __future__ import annotations

from cli.auth.login import logout
from cli.services.events.list_events import list_events
from security.auth_session import get_auth
from security.authorization import Role
from services.usecases.event_crud import EventService

from cli.services.events.update_event_form import update_event_form_support


def support_menu() -> None:
    """
    Menu CLI pour le rôle SUPPORT.

    - (1) Lister uniquement les événements assignés à l'utilisateur connecté
    - (2) Mettre à jour un événement assigné (dates, lieu, notes, participants)
    """
    while True:
        auth = get_auth()
        if not auth:
            print("❌ Session expirée ou non connectée. Merci de vous reconnecter.")
            return
        if auth.role not in (Role.SUPPORT, Role.GESTION):
            print("⛔ Accès refusé : ce menu est réservé aux rôles SUPPORT / GESTION.")
            return

        print("\n" + "=" * 50)
        print("🧭 MENU SUPPORT".center(50))
        print("=" * 50)
        print("1. Lister MES événements (assignés à moi)")
        print("2. Mettre à jour un de MES événements")
        print("3. Se déconnecter")
        print("0. Retour")

        choice = input("\nVotre choix : ").strip()

        if choice == "1":
            try:
                list_events(
                    service=EventService(),
                    auth=auth,
                    display=True,
                    as_table=True,
                    support_only_mine=True,  # ← filtre “assignés à moi”
                )
            except Exception as e:
                print(f"❌ Impossible d’afficher : {e}")

        elif choice == "2":
            try:
                update_event_form_support(service=EventService(), auth=auth)
            except Exception as e:
                print(f"❌ Erreur pendant la mise à jour : {e}")

        elif choice == "3":
            logout()
            print("✅ Déconnecté avec succès.")
            return

        elif choice == "0":
            return

        else:
            print("❌ Choix invalide. Réessayez.")