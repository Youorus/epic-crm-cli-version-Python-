# cli/services/users/create_user_form.py
from __future__ import annotations

import os
import re
import hashlib
from getpass import getpass
from datetime import datetime, timezone
from typing import Optional

from enums.user_role import UserRole
from models.users import User
from security.authorization import AuthContext, AuthzError, Role
from services.usecases.user_crud import UserService
from services.crud.user_repo import UserRepo
from services.db_session import session_scope


# ─────────────────────────────────────────────────────────
# Helpers validations / sécurité
# ─────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(email: str) -> None:
    if not email or not _EMAIL_RE.match(email):
        raise ValueError("Adresse email invalide.")


def _choose_role() -> UserRole:
    """Propose la sélection du rôle à partir de UserRole."""
    roles = list(UserRole)
    print("\n   🔐 Choisissez un rôle :")
    for i, r in enumerate(roles, start=1):
        print(f"   {i}. {r.name}")
    while True:
        raw = input("   Votre choix (1..n) : ").strip()
        if raw.lower() == "retour":
            raise KeyboardInterrupt
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(roles):
                return roles[idx - 1]
        print("   ❌ Choix invalide.")


def _yes_no(prompt: str, default: bool = True) -> bool:
    suf = "[O/n]" if default else "[o/N]"
    while True:
        s = input(f"   {prompt} {suf} : ").strip().lower()
        if s == "":
            return default
        if s in ("o", "oui", "y", "yes", "1", "true"):
            return True
        if s in ("n", "non", "no", "0", "false"):
            return False
        print("   ❌ Réponse invalide. Tapez o/n.")


def _hash_password(password: str) -> tuple[bytes, bytes]:
    """
    Hash minimaliste (scrypt) si ton domaine n'expose pas user.set_password().
    Retourne (salt, hash).
    """
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return salt, dk


def _set_password_on_user(u: User, password: str) -> None:
    """
    Essaie d'utiliser u.set_password(); sinon renseigne _password_salt/_password_hash.
    """
    if hasattr(u, "set_password") and callable(getattr(u, "set_password")):
        u.set_password(password)  # type: ignore[attr-defined]
        return
    # fallback privé si le domaine ne fournit pas set_password
    salt, h = _hash_password(password)
    setattr(u, "_password_salt", salt)
    setattr(u, "_password_hash", h)


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