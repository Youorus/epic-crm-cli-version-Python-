# cli/menus/commercial_menu.py
from __future__ import annotations

from cli.auth.login import logout
from cli.services.events.create_event_form import create_event_form
from security.auth_session import get_auth
from security.authorization import Role

# Use-cases (domaine)
from services.usecases.client_crud import ClientService
from services.usecases.contract_crud import ContractService
from services.usecases.event_crud import EventService

# Services CLI (affichage / formulaires)
from cli.services.clients.list_clients import list_clients
from cli.services.clients.create_client_form import create_client_form
from cli.services.clients.update_client_form import update_client_form
from cli.services.contracts.list_contracts import list_contracts


def commercial_menu() -> None:
    """
    Menu principal pour un utilisateur au rôle COMMERCIAL.

    Actions :
      1) Lister mes clients (filtrés par rôle côté service)
      2) Créer un client (auto-assignation au commercial connecté)
      3) Mettre à jour un de mes clients
      4) Lister mes contrats
      5) Lister mes contrats non signés
      6) Lister mes contrats avec montant dû > 0
      7) Créer un événement pour un contrat signé
      9) Déconnexion
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
        print("9. Déconnexion")
        print("0. Retour")

        choice = input("\nVotre choix : ").strip()

        if choice == "1":
            try:
                list_clients(service=ClientService(), auth=auth, display=True, as_table=True)
            except Exception as e:
                print(f"❌ Impossible d’afficher les clients : {e}")

        elif choice == "2":
            try:
                create_client_form(service=ClientService(), auth=auth)
            except Exception as e:
                print(f"❌ Erreur pendant la création du client : {e}")

        elif choice == "3":
            try:
                update_client_form(service=ClientService(), auth=auth)
            except Exception as e:
                print(f"❌ Erreur pendant la mise à jour du client : {e}")

        elif choice == "4":
            try:
                list_contracts(service=ContractService(), auth=auth, display=True, as_table=True)
            except Exception as e:
                print(f"❌ Impossible d’afficher les contrats : {e}")

        elif choice == "5":
            try:
                list_contracts(
                    service=ContractService(),
                    auth=auth,
                    display=True,
                    as_table=True,
                    filter_signed=False,
                )
            except Exception as e:
                print(f"❌ Impossible d’afficher les contrats non signés : {e}")

        elif choice == "6":
            try:
                list_contracts(
                    service=ContractService(),
                    auth=auth,
                    display=True,
                    as_table=True,
                    min_due=0.01,
                )
            except Exception as e:
                print(f"❌ Impossible d’afficher les contrats avec reste dû : {e}")

        elif choice == "7":
            try:
                create_event_form(
                    event_service=EventService(),
                    contract_service=ContractService(),
                    auth=auth,
                )
            except Exception as e:
                print(f"❌ Erreur lors de la création de l'événement : {e}")

        elif choice == "9":
            logout()
            print("✅ Déconnecté avec succès.")
            return

        elif choice == "0":
            return

        else:
            print("❌ Choix invalide. Réessayez.")