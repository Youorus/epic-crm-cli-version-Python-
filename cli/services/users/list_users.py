from typing import Optional
from tabulate import tabulate

from security.authorization import can_read_users
from services.usecases.user_crud import UserService
from security.auth_session import AuthContext


def list_users(
        service: UserService,
        auth: AuthContext,
        display: bool = True,
        as_table: bool = True
):
    """
    Liste tous les collaborateurs (utilisateurs) avec filtrage selon les droits.

    :param service: Instance de UserService pour la gestion des utilisateurs
    :param auth: AuthContext de l'utilisateur connecté
    :param display: True pour afficher directement les données
    :param as_table: True pour format tableau (sinon print brut)
    :return: Liste des utilisateurs (dictionnaires ou objets)
    """
    try:
        # Vérification des permissions
        if not can_read_users(auth):
            print("⛔ Accès refusé : vous n'avez pas les droits pour lister les collaborateurs.")
            return []

        # Récupération des utilisateurs via le service
        users = service.list(auth=auth)

        # Si aucun utilisateur trouvé
        if not users:
            print("ℹ️ Aucun collaborateur trouvé.")
            return []

        # Affichage
        if display:
            if as_table:
                headers = ["ID", "Nom", "Prénom", "Email", "Rôle", "Actif"]
                rows = [
                    [
                        u.id,
                        u.username or "",
                        u.email,
                        u.role,
                        u.created_at,
                        "✅" if u.is_active else "❌"
                    ]
                    for u in users
                ]
                print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))
            else:
                for u in users:
                    print(f"- {u.id}: {u.first_name} {u.last_name} ({u.role})")

        return users

    except Exception as e:
        print(f"❌ Erreur inattendue lors du listing des collaborateurs : {e}")
        return []