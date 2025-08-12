# cli/menus/gestion_menu.py
from __future__ import annotations

from cli.auth.login import logout
from cli.services.users.update_contract_form import update_contract_form
# --- Auth / session ---
from security.auth_session import get_auth
from security.authorization import Role

# --- Use-cases (métier, Python pur) ---
from services.usecases.client_crud import ClientService
from services.usecases.contract_crud import ContractService
from services.usecases.event_crud import EventService
from services.usecases.user_crud import UserService

# --- Services CLI (affichages + formulaires) ---
from cli.services.clients.list_clients import list_clients
from cli.services.contracts.list_contracts import list_contracts
from cli.services.contracts.create_contract_form import create_contract_form
from cli.services.events.list_events import list_events
from cli.services.events.assign_support_form import assign_support_to_event_form
from cli.services.users.list_users import list_users
from cli.services.users.create_user_form import create_user_form
from cli.services.users.update_user_form import update_user_form
from cli.services.users.delete_user_form import delete_user_form


def gestion_menu() -> None:
    """
    Menu principal pour un utilisateur au rôle GESTION.
    Propose :
      1) Lister clients
      2) Lister contrats
      3) Créer contrat
      4) Modifier contrat
      5) Lister événements
      6) Lister événements sans support
      7) Assigner un support à un événement
      8) Créer un collaborateur
      9) Modifier un collaborateur
     10) Supprimer un collaborateur
     11) Lister les collaborateurs
     12) Se déconnecter
      0) Retour
    """
    while True:
        # Rafraîchit l'auth à chaque boucle (token potentiellement rafraîchi)
        auth = get_auth()
        if not auth:
            print("❌ Session expirée ou non connectée. Merci de vous reconnecter.")
            return
        if auth.role != Role.GESTION:  # garde défensive
            print("⛔ Accès refusé : ce menu est réservé au rôle GESTION.")
            return

        print("\n" + "=" * 50)
        print("🧭 MENU GESTION".center(50))
        print("=" * 50)
        print("1.  Lister tous les clients")
        print("2.  Lister tous les contrats")
        print("3.  Créer un contrat")
        print("4.  Modifier un contrat")
        print("5.  Lister tous les événements")
        print("6.  Lister les événements sans support")
        print("7.  Assigner un support à un événement")
        print("8.  Créer un collaborateur")
        print("9.  Modifier un collaborateur")
        print("10. Supprimer un collaborateur")
        print("11. Lister les collaborateurs")
        print("12. Se déconnecter")
        print("0.  Retour")

        choice = input("\nVotre choix : ").strip()

        # 1) Clients
        if choice == "1":
            try:
                list_clients(service=ClientService(), auth=auth, display=True, as_table=True)
            except Exception as e:
                print(f"❌ Impossible d’afficher les clients : {e}")

        # 2) Contrats
        elif choice == "2":
            try:
                list_contracts(service=ContractService(), auth=auth, display=True, as_table=True)
            except Exception as e:
                print(f"❌ Impossible d’afficher les contrats : {e}")

        # 3) Création d’un contrat
        elif choice == "3":
            try:
                create_contract_form(service=ContractService(), auth=auth)
            except Exception as e:
                print(f"❌ Erreur pendant la création du contrat : {e}")

        # 4) Modification d’un contrat
        elif choice == "4":
            try:
                update_contract_form(service=ContractService(), auth=auth)
            except Exception as e:
                print(f"❌ Erreur pendant la modification : {e}")

        # 5) Événements (tous)
        elif choice == "5":
            try:
                list_events(service=EventService(), auth=auth, display=True, as_table=True)
            except Exception as e:
                print(f"❌ Impossible d’afficher les événements : {e}")

        # 6) Événements sans support
        elif choice == "6":
            try:
                list_events(
                    service=EventService(),
                    auth=auth,
                    display=True,
                    as_table=True,
                    support_isnull=True,  # filtre "sans support"
                )
            except Exception as e:
                print(f"❌ Impossible d’afficher les événements sans support : {e}")

        # 7) Assigner un support à un événement
        elif choice == "7":
            try:
                assign_support_to_event_form(
                    event_service=EventService(),
                    user_service=UserService(),
                    auth=auth,
                )
            except Exception as e:
                print(f"❌ Erreur pendant l’assignation : {e}")

        # 8) Création collaborateur
        elif choice == "8":
            try:
                create_user_form(service=UserService(), auth=auth)
            except Exception as e:
                print(f"❌ Erreur pendant la création du collaborateur : {e}")

        # 9) Modification collaborateur
        elif choice == "9":
            try:
                update_user_form(service=UserService(), auth=auth)
            except Exception as e:
                print(f"❌ Erreur pendant la modification du collaborateur : {e}")

        # 10) Suppression collaborateur
        elif choice == "10":
            try:
                delete_user_form(service=UserService(), auth=auth)
            except Exception as e:
                print(f"❌ Erreur pendant la suppression du collaborateur : {e}")

        # 11) Lister collaborateurs
        elif choice == "11":
            try:
                list_users(service=UserService(), auth=auth, display=True, as_table=True)
            except Exception as e:
                print(f"❌ Impossible d’afficher les collaborateurs : {e}")

        # 12) Logout
        elif choice == "12":
            logout()    # vide les tokens
            return      # on remonte au routeur (ou on quitte)

        # Quitter le menu Gestion (retour au routeur)
        elif choice == "0":
            return

        else:
            print("❌ Choix invalide. Réessayez.")