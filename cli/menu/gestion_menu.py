# cli/menus/gestion_menu.py
from __future__ import annotations

# ⛔️ Imports d’actions volontairement commentés pour éviter toute exécution.
#    Décommente-les quand tu veux activer les options correspondantes.
# from cli.forms.contracts.contract_update_form import create_contract_form
# from cli.forms.contracts.update_contract_form import update_contract_form
# from cli.forms.users.create_user_form import create_user_form
# from cli.forms.users.user_update_form import update_user_form
# from cli.forms.users.user_delete_form import delete_user_form
# from cli.services.clients.get_clients import list_clients
# from cli.services.contracts.get_contracts import list_contracts
# from cli.services.events.get_events import list_events
# from cli.services.events.update_support_event import update_support_event
# from cli.utils.session import session
# from cli.utils.config import EVENT_URL


def gestion_menu() -> None:
    """
    Menu principal pour un utilisateur au rôle GESTION.

    Les actions sont volontairement COMMENTÉES pour :
      - permettre une démo/présentation sans effet de bord ;
      - t’éviter des imports non utilisés ou des appels réseau involontaires.

    Pour activer une option :
      1) Décommente l’import correspondant en haut du fichier.
      2) Décommente l’appel dans le bloc `if choice == "...":`.
    """
    while True:
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

        # 1) Clients — listing
        if choice == "1":
            print("ℹ️ Action désactivée (listing clients).")
            # list_clients(display=True)

        # 2) Contrats — listing
        elif choice == "2":
            print("ℹ️ Action désactivée (listing contrats).")
            # list_contracts(display=True)

        # 3) Créer un contrat
        elif choice == "3":
            print("ℹ️ Action désactivée (création contrat).")
            # create_contract_form()

        # 4) Modifier un contrat par ID
        elif choice == "4":
            print("ℹ️ Action désactivée (modification contrat).")
            # while True:
            #     cid = input("ID du contrat à modifier (ou 'retour') : ").strip()
            #     if cid.lower() == "retour":
            #         break
            #     if cid.isdigit():
            #         update_contract_form(int(cid))
            #         break
            #     print("❌ L’ID doit être un entier.")

        # 5) Événements — listing complet
        elif choice == "5":
            print("ℹ️ Action désactivée (listing événements).")
            # list_events(display=True)

        # 6) Événements sans support
        elif choice == "6":
            print("ℹ️ Action désactivée (événements sans support).")
            # list_events(params={"support_contact__isnull": "true"}, display=True)

        # 7) Assigner un support à un événement
        elif choice == "7":
            print("ℹ️ Action désactivée (assignation support).")
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

        # 8) Créer un collaborateur
        elif choice == "8":
            print("ℹ️ Action désactivée (création collaborateur).")
            # create_user_form()

        # 9) Modifier un collaborateur
        elif choice == "9":
            print("ℹ️ Action désactivée (modification collaborateur).")
            # update_user_form()

        # 10) Supprimer un collaborateur
        elif choice == "10":
            print("ℹ️ Action désactivée (suppression collaborateur).")
            # delete_user_form()

        # Retour
        elif choice == "0":
            return

        # Choix invalide
        else:
            print("❌ Choix invalide. Réessayez.")