# cli/menus/gestion_menu.py
from __future__ import annotations

from typing import Optional

from security.auth_session import get_auth
from services.usecases.client_crud import ClientService
from cli.services.clients.list_clients import list_clients as cli_list_clients


def gestion_menu() -> None:
    """
    Menu principal pour un utilisateur au rôle GESTION.
    Certaines actions restent commentées pour éviter des effets de bord pendant la démo.
    Décommente les imports + les blocs si tu veux les activer.
    """
    while True:
        # Récupère l'auth à chaque itération (token potentiellement rafraîchi / user switch)
        auth = get_auth()
        if not auth:
            print("❌ Session expirée ou non connectée. Merci de vous reconnecter.")
            return
        if auth.role != auth.role.GESTION:  # garde défensive
            print("⛔ Accès refusé : ce menu est réservé au rôle GESTION.")
            return

        print("\n" + "=" * 50)
        print("🧭 MENU GESTION".center(50))
        print("=" * 50)
        print("1. Lister tous les clients")
        print("2. Lister tous les contrats")
        print("3. Créer un contrat")
        print("4. Modifier un contrat")
        print("5. Lister tous les événements")
        print("6. Filtrer événements sans support")
        print("7. Assigner un support à un événement")
        print("8. Créer un collaborateur")
        print("9. Modifier un collaborateur")
        print("10. Supprimer un collaborateur")
        print("0. Retour")

        choice = input("\nVotre choix : ").strip()

        if choice == "1":
            # Liste via use case (droits & filtrage côté service)
            try:
                service = ClientService()
                cli_list_clients(service=service, auth=auth, display=True, as_table=True)
            except Exception as e:
                print(f"❌ Impossible d’afficher les clients : {e}")

        elif choice == "2":
            print("ℹ️ Action désactivée (listing contrats).")
            # from cli.services.contracts.get_contracts import list_contracts
            # list_contracts(display=True)

        elif choice == "3":
            print("ℹ️ Action désactivée (création contrat).")
            # from cli.forms.contracts.contract_update_form import create_contract_form
            # create_contract_form()

        elif choice == "4":
            print("ℹ️ Action désactivée (modification contrat).")
            # from cli.forms.contracts.update_contract_form import update_contract_form
            # while True:
            #     cid = input("ID du contrat à modifier (ou 'retour') : ").strip()
            #     if cid.lower() == "retour":
            #         break
            #     if cid.isdigit():
            #         update_contract_form(int(cid))
            #         break
            #     print("❌ L’ID doit être un entier.")

        elif choice == "5":
            print("ℹ️ Action désactivée (listing événements).")
            # from cli.services.events.get_events import list_events
            # list_events(display=True)

        elif choice == "6":
            print("ℹ️ Action désactivée (événements sans support).")
            # from cli.services.events.get_events import list_events
            # list_events(params={"support_contact__isnull": "true"}, display=True)

        elif choice == "7":
            print("ℹ️ Action désactivée (assignation support).")
            # from cli.services.events.update_support_event import update_support_event
            # from cli.utils.session import session
            # from cli.utils.config import EVENT_URL
            # event_id, payload = update_support_event()
            # if event_id and payload:
            #     resp = session.patch(f"{EVENT_URL}{event_id}/", json=payload)
            #     if 200 <= resp.status_code < 300:
            #         print(f"✅ Support assigné à l’événement #{event_id}.")
            #     else:
            #         try:
            #             print("❌ Erreur :", resp.status_code, resp.json())
            #         except ValueError:
            #             print("❌ Erreur :", resp.status_code, resp.text)

        elif choice == "8":
            print("ℹ️ Action désactivée (création collaborateur).")
            # from cli.forms.users.create_user_form import create_user_form
            # create_user_form()

        elif choice == "9":
            print("ℹ️ Action désactivée (modification collaborateur).")
            # from cli.forms.users.user_update_form import update_user_form
            # update_user_form()

        elif choice == "10":
            print("ℹ️ Action désactivée (suppression collaborateur).")
            # from cli.forms.users.user_delete_form import delete_user_form
            # delete_user_form()

        elif choice == "0":
            return

        else:
            print("❌ Choix invalide. Réessayez.")