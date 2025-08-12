# cli/menus/commercial_menu.py
from __future__ import annotations

# ⛔️ Imports d’actions volontairement commentés pour éviter toute exécution.
#    Décommente-les quand tu veux activer les options correspondantes.
# from cli.services.clients.get_clients import list_clients
# from cli.services.contracts.get_contracts import list_contracts
# from cli.forms.clients.create_client_form import create_client_form
# from cli.forms.clients.update_client_form import update_client_form
# from cli.forms.events.create_event_form import create_event_form


def commercial_menu() -> None:
    """
    Menu principal pour un utilisateur au rôle COMMERCIAL.

    Les actions sont COMMENTÉES pour permettre une présentation/démo sans effet de bord.
    Pour activer une option :
      1) Décommente l’import correspondant en haut du fichier.
      2) Décommente l’appel dans le bloc `if choice == "...":`.
    """
    while True:
        print("\n" + "=" * 50)
        print("🧭 MENU COMMERCIAL".center(50))
        print("=" * 50)
        print("1. Lister mes clients")
        print("2. Créer un client")
        print("3. Mettre à jour un de mes clients")
        print("4. Lister mes contrats")
        print("5. Contrats non signés")
        print("6. Modifier un de mes contrats")
        print("7. Créer un événement (pour un contrat signé)")
        print("0. Retour")

        choice = input("\nVotre choix : ").strip()

        # 1) Lister les clients (restriction côté API par rôle)
        if choice == "1":
            print("ℹ️ Action désactivée (listing de TES clients).")
            # list_clients(display=True)  # ou avec filtre si tu as prévu un param : params={"sales_contact": "self"}

        # 2) Créer un client (formulaire → POST)
        elif choice == "2":
            print("ℹ️ Action désactivée (création client).")
            # create_client_form()

        # 3) Mettre à jour un client (formulaire → PATCH)
        elif choice == "3":
            print("ℹ️ Action désactivée (modification d’un de TES clients).")
            # cid = input("ID du client à modifier (ou 'retour') : ").strip()
            # if cid.lower() != "retour" and cid.isdigit():
            #     update_client_form(int(cid))
            # elif cid.lower() != "retour":
            #     print("❌ L’ID doit être un entier.")

        # 4) Lister les contrats (restriction par rôle côté API)
        elif choice == "4":
            print("ℹ️ Action désactivée (listing de TES contrats).")
            # list_contracts(display=True)

        # 5) Lister uniquement les contrats NON signés
        elif choice == "5":
            print("ℹ️ Action désactivée (contrats non signés).")
            # list_contracts(params={"is_signed": "false"}, display=True)

        # 6) (Intitulé historique) — dans la version active tu listais ceux avec montant dû > 0
        elif choice == "6":
            print("ℹ️ Action désactivée (contrats avec montant dû > 0).")
            # list_contracts(params={"amount_due__gt": "0"}, display=True)

        # 7) Créer un événement pour un contrat SIGNÉ
        elif choice == "7":
            print("ℹ️ Action désactivée (création d’événement pour contrat signé).")
            # signed_contracts = list_contracts(params={"is_signed": "true"}, display=False)
            # if not signed_contracts:
            #     print("ℹ️ Aucun contrat signé disponible.")
            # else:
            #     create_event_form(signed_contracts)

        # Retour
        elif choice == "0":
            return

        # Choix invalide
        else:
            print("❌ Choix invalide. Réessayez.")