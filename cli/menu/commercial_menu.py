# cli/menus/commercial_menu.py
from __future__ import annotations

from security.auth_session import get_auth
from security.authorization import Role

# Use-cases (domaine)
from services.usecases.client_crud import ClientService
from services.usecases.contract_crud import ContractService
# from services.usecases.event_crud import EventService  # à activer si tu ajoutes la création d'événement

# Services CLI (affichage / formulaires)
from cli.services.clients.list_clients import list_clients
from cli.services.clients.create_client_form import create_client_form
from cli.services.clients.update_client_form import update_client_form
from cli.services.contracts.list_contracts import list_contracts
# from cli.services.events.create_event_form import create_event_form  # à activer si dispo


def commercial_menu() -> None:
    """
    Menu principal pour un utilisateur au rôle COMMERCIAL.

    Actions :
      1) Lister mes clients (le filtrage par rôle est fait côté service)
      2) Créer un client (auto-assignation au commercial connecté)
      3) Mettre à jour un de MES clients
      4) Lister MES contrats
      5) Lister MES contrats non signés
      6) Lister MES contrats avec montant dû > 0
      7) (prévu) Créer un événement pour un contrat signé
      0) Retour
    """
    while True:
        auth = get_auth()
        if not auth:
            print("❌ Session expirée ou non connectée. Merci de vous reconnecter.")
            return
        if auth.role is not Role.COMMERCIAL:
            print("⛔ Accès refusé : ce menu est réservé au rôle COMMERCIAL.")
            return

        print("\n" + "=" * 50)
        print("🧭 MENU COMMERCIAL".center(50))
        print("=" * 50)
        print("1. Lister mes clients")
        print("2. Créer un client")
        print("3. Mettre à jour un de mes clients")
        print("4. Lister mes contrats")
        print("5. Contrats non signés")
        print("6. Contrats avec montant dû > 0")
        print("7. Créer un événement (pour un contrat signé)")
        print("0. Retour")

        choice = input("\nVotre choix : ").strip()

        # 1) Lister MES clients
        if choice == "1":
            try:
                # Le service applique les permissions : un COMMERCIAL ne voit que ses clients
                list_clients(service=ClientService(), auth=auth, display=True, as_table=True)
            except Exception as e:
                print(f"❌ Impossible d’afficher les clients : {e}")

        # 2) Créer un client (auto-assignation au commercial connecté)
        elif choice == "2":
            try:
                create_client_form(service=ClientService(), auth=auth)
            except Exception as e:
                print(f"❌ Erreur pendant la création du client : {e}")

        # 3) Mettre à jour un de MES clients
        elif choice == "3":
            try:
                update_client_form(service=ClientService(), auth=auth)
            except Exception as e:
                print(f"❌ Erreur pendant la mise à jour du client : {e}")

        # 4) Lister MES contrats
        elif choice == "4":
            try:
                list_contracts(service=ContractService(), auth=auth, display=True, as_table=True)
            except Exception as e:
                print(f"❌ Impossible d’afficher les contrats : {e}")

        # 5) MES contrats non signés
        elif choice == "5":
            try:
                list_contracts(
                    service=ContractService(),
                    auth=auth,
                    display=True,
                    as_table=True,
                    filter_signed=False,   # ← uniquement non signés
                )
            except Exception as e:
                print(f"❌ Impossible d’afficher les contrats non signés : {e}")

        # 6) MES contrats avec montant dû > 0
        elif choice == "6":
            try:
                list_contracts(
                    service=ContractService(),
                    auth=auth,
                    display=True,
                    as_table=True,
                    min_due=0.01,          # ← montant dû strictement positif
                )
            except Exception as e:
                print(f"❌ Impossible d’afficher les contrats avec reste dû : {e}")

        # 7) Créer un événement pour un contrat signé
        elif choice == "7":
            print("ℹ️ Cette fonctionnalité nécessite un formulaire de création d’événement.")
            print("   Branche `create_event_form(...)` quand ton module est prêt.")
            # Exemple quand tu auras le form :
            # try:
            #     signed_contracts = list_contracts(
            #         service=ContractService(),
            #         auth=auth,
            #         display=False,
            #         filter_signed=True,
            #     )
            #     if not signed_contracts:
            #         print("ℹ️ Aucun contrat signé disponible.")
            #     else:
            #         create_event_form(signed_contracts=signed_contracts, auth=auth, event_service=EventService())
            # except Exception as e:
            #     print(f"❌ Erreur pendant la création d’événement : {e}")

        # 0) Retour
        elif choice == "0":
            return

        else:
            print("❌ Choix invalide. Réessayez.")