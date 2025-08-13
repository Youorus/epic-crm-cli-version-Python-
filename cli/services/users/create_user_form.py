# cli/services/user/create_user_form.py
from __future__ import annotations


from getpass import getpass

from typing import Optional

from cli.services.users.utils import _validate_email, _choose_role, _yes_no, _set_password_on_user
from models.users import User
from security.authorization import AuthContext, AuthzError, Role
from services.usecases.user_crud import UserService
from services.crud.user_repo import UserRepo
from services.db_session import session_scope

# ─────────────────────────────────────────────────────────
# Formulaire principal
# ─────────────────────────────────────────────────────────
def create_user_form(
    *,
    service: UserService,
    auth: AuthContext,
) -> Optional[User]:
    """
    Formulaire CLI pour créer un collaborateur.
    - Unicité username & email (vérif via UserRepo)
    - Rôle (UserRole)
    - Mot de passe saisi 2x et hashé (scrypt si pas de set_password)
    - Champs "admin" optionnels (is_staff, is_superuser)
    - Défense côté CLI : réservé à la GESTION
    """
    print("\n" + "=" * 50)
    print("👤  CRÉATION D’UN COLLABORATEUR".center(50))
    print("=" * 50)
    print("(Tapez 'retour' à tout moment pour annuler.)\n")

    # Défense côté CLI (la permission réelle reste dans UserService)
    if hasattr(auth, "role") and auth.role != Role.GESTION:
        print("⛔ Accès refusé : seule la GESTION peut créer un collaborateur.")
        return None

    # 1) Username
    while True:
        username = input("   🧑  Nom d’utilisateur : ").strip()
        if username.lower() == "retour":
            print("   ❌ Création annulée.")
            return None
        if not username:
            print("   ❌ Le nom d’utilisateur est requis.")
            continue

        with session_scope() as s:
            repo = UserRepo(s)
            if repo.get_by_username(username):
                print("   ❌ Ce nom d’utilisateur existe déjà.")
                continue
        break

    # 2) Email
    while True:
        email = input("   📧 Email : ").strip()
        if email.lower() == "retour":
            print("   ❌ Création annulée.")
            return None
        try:
            _validate_email(email)
        except ValueError as e:
            print(f"   ❌ {e}")
            continue

        with session_scope() as s:
            repo = UserRepo(s)
            if repo.get_by_email(email):
                print("   ❌ Cet email est déjà utilisé.")
                continue
        break

    # 3) Rôle
    try:
        role = _choose_role()
    except KeyboardInterrupt:
        print("   ❌ Création annulée.")
        return None

    # 4) Mot de passe
    while True:
        pwd1 = getpass("   🔒 Mot de passe : ").strip()
        if pwd1.lower() == "retour":
            print("   ❌ Création annulée.")
            return None
        if len(pwd1) < 8:
            print("   ❌ Mot de passe trop court (8+ caractères).")
            continue
        pwd2 = getpass("   🔒 Confirmation : ").strip()
        if pwd1 != pwd2:
            print("   ❌ Les mots de passe ne correspondent pas.")
            continue
        break

    # 5) Flags (optionnels)
    is_active = _yes_no("Activer le compte ?", True)
    is_staff = _yes_no("Marquer staff (accès outils internes) ?", False)
    is_superuser = _yes_no("Superuser (⚠︎ privilèges étendus) ?", False)

    # 6) Récap
    print("\n" + "-" * 50)
    print("📋  RÉCAPITULATIF DU COLLABORATEUR".center(50))
    print("-" * 50)
    print(f"   🧑  Username  : {username}")
    print(f"   📧 Email     : {email}")
    print(f"   🔐 Rôle      : {role.name}")
    print(f"   ✅ Actif     : {'Oui' if is_active else 'Non'}")
    print(f"   🛠  Staff     : {'Oui' if is_staff else 'Non'}")
    print(f"   👑 Superuser : {'Oui' if is_superuser else 'Non'}")
    print("-" * 50)
    if input("   Confirmer la création ? (o/N) : ").strip().lower() != "o":
        print("   ❌ Création annulée.")
        return None

    # 7) Construction entité (laisse date_joined/created_at à None -> DB defaults)
    u = User(
        id=None,
        username=username,
        email=email,
        role=role,
        is_active=is_active,
        is_staff=is_staff,
        is_superuser=is_superuser,
    )
    _set_password_on_user(u, pwd1)

    # 8) Appel use-case (vérifie autorisation + persiste via repo)
    try:
        created = service.create(u, auth=auth)
        print(f"✅ Collaborateur #{created.id} créé avec succès ({created.username} — {created.role.name}).")
        return created
    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
    except Exception as e:
        print(f"❌ Erreur lors de la création : {e}")

    return None