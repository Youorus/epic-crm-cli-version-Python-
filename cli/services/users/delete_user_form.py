# cli/forms/users/delete_user_form.py
from __future__ import annotations

from cli.services.users.utils import _input_id_or_retour
from enums.user_role import UserRole
from security.authorization import AuthContext, AuthzError, can_delete_user
from services.usecases.user_crud import UserService
from services.db_session import session_scope
from services.crud.user_repo import UserRepo





def delete_user_form(*, service: UserService, auth: AuthContext) -> None:
    print("\n" + "=" * 50)
    print("        🗑️  SUPPRESSION D’UN COLLABORATEUR        ".center(50))
    print("=" * 50)
    print("(Tapez 'retour' à tout moment pour annuler.)\n")

    # Optionnel : rappeler les IDs existants avant saisie
    try:
        with session_scope() as s:
            repo = UserRepo(s)
            users = list(repo.list())
        if users:
            print("   Utilisateurs existants :")
            for u in users:
                print(f"   - #{u.id} {u.username} <{u.email}> [{u.role.value}]")
            print()
    except Exception:
        # ne pas bloquer la suite si la liste échoue
        pass

    uid = _input_id_or_retour("   🔢 ID du collaborateur à supprimer : ")
    if uid is None:
        print("   ❌ Suppression annulée.")
        return

    print(f"[DEBUG] Suppression ID={uid}, Auth role={auth.role}")

    # Récupération de l’utilisateur avant vérification d’autorisation
    with session_scope() as s:
        repo = UserRepo(s)
        target = repo.get_by_id(uid)

    if not target:
        print("   ❌ Collaborateur introuvable.")
        return

    # Règle d’auto-protection : on évite la suppression de soi-même (optionnel)
    if getattr(auth, "user_id", None) == target.id:
        print("   ⛔ Vous ne pouvez pas vous supprimer vous-même.")
        return

    # Vérifie l’autorisation explicite (distinction claire des erreurs)
    if not can_delete_user(auth, user=target):
        print("   ⛔ Accès refusé : vous n’êtes pas autorisé à supprimer cet utilisateur.")
        return

    print("\n" + "-" * 50)
    print("                 📋  INFORMATIONS                  ")
    print("-" * 50)
    print(f"   🆔 ID         : {target.id}")
    print(f"   🧑  Username  : {target.username}")
    print(f"   📧 Email     : {target.email}")
    print(f"   🔐 Rôle      : {target.role.value}")
    print(f"   ✅ Actif     : {'Oui' if target.is_active else 'Non'}")
    print(f"   🛠  Staff     : {'Oui' if target.is_staff else 'Non'}")
    print(f"   👑 Superuser : {'Oui' if target.is_superuser else 'Non'}")

    confirm = input("   Confirmer la suppression ? (o/N) : ").strip().lower()
    if confirm != "o":
        print("   ❌ Suppression annulée.")
        return

    try:
        service.delete(user_id=uid, auth=auth)
        print("   ✅ Collaborateur supprimé.")
    except AuthzError as e:
        print(f"   ⛔ Accès refusé : {e}")
    except Exception as e:
        print(f"   ❌ Erreur lors de la suppression : {e}")