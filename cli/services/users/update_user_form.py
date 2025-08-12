# cli/services/users/update_user_form.py
from __future__ import annotations

import os
import re
import hashlib
from getpass import getpass
from typing import Optional

from enums.user_role import UserRole
from models.users import User
from security.authorization import AuthContext, AuthzError, Role
from services.usecases.user_crud import UserService
from services.crud.user_repo import UserRepo
from services.db_session import session_scope


# ─────────────────────────────────────────────────────────
# Helpers validations / UI
# ─────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(email: str) -> None:
    if not email or not _EMAIL_RE.match(email):
        raise ValueError("Adresse email invalide.")


def _input_int(prompt: str) -> Optional[int]:
    s = input(prompt).strip()
    if s.lower() == "retour":
        return None
    if not s.isdigit():
        print("   ❌ L’ID doit être un entier.")
        return _input_int(prompt)
    return int(s)


def _prompt_keep_or_change(prompt: str, current: str) -> str:
    """
    Affiche la valeur actuelle et permet de la modifier.
    Entrée vide → on garde la valeur courante.
    """
    s = input(f"   {prompt} [{current}] : ").strip()
    if s.lower() == "retour":
        raise KeyboardInterrupt
    return current if s == "" else s


def _choose_role(default: UserRole) -> UserRole:
    roles = list(UserRole)
    print("\n   🔐 Rôle courant :", default.name)
    for i, r in enumerate(roles, start=1):
        print(f"   {i}. {r.name}")
    while True:
        raw = input(f"   Choisir un rôle (1..{len(roles)}) [Enter pour garder {default.name}] : ").strip()
        if raw.lower() == "retour":
            raise KeyboardInterrupt
        if raw == "":
            return default
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(roles):
                return roles[idx - 1]
        print("   ❌ Choix invalide.")


def _yes_no(prompt: str, default: bool) -> bool:
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


# ─────────────────────────────────────────────────────────
# Password (fallback scrypt si pas de set_password)
# ─────────────────────────────────────────────────────────
def _hash_password(password: str) -> tuple[bytes, bytes]:
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return salt, dk


def _set_password_on_user(u: User, password: str) -> None:
    """
    Utilise u.set_password() si disponible. Sinon, renseigne _password_salt/_password_hash.
    """
    if hasattr(u, "set_password") and callable(getattr(u, "set_password")):
        u.set_password(password)  # type: ignore[attr-defined]
        return
    salt, h = _hash_password(password)
    setattr(u, "_password_salt", salt)
    setattr(u, "_password_hash", h)


# ─────────────────────────────────────────────────────────
# Formulaire principal
# ─────────────────────────────────────────────────────────
def update_user_form(
    *,
    service: UserService,
    auth: AuthContext,
) -> Optional[User]:
    """
    Formulaire CLI pour modifier un collaborateur.
    - Saisie de l'ID, chargement de l'utilisateur existant.
    - Modification des champs : username, email, rôle, is_active, is_staff, is_superuser.
    - Password : changement optionnel (saisi 2x).
    - Vérifs d’unicité (username/email) si modifiés.
    - Défense côté CLI : réservé à la GESTION (l’autorisation réelle est gérée par UserService.update).
    """
    print("\n" + "=" * 50)
    print("✏️  MODIFICATION D’UN COLLABORATEUR".center(50))
    print("=" * 50)
    print("(Tapez 'retour' à tout moment pour annuler.)\n")

    # Défense côté CLI
    if hasattr(auth, "role") and auth.role != Role.GESTION:
        print("⛔ Accès refusé : seule la GESTION peut modifier un collaborateur.")
        return None

    # 1) ID à modifier
    user_id = _input_int("   🔢 ID du collaborateur : ")
    if user_id is None:
        print("   ❌ Opération annulée.")
        return None

    # 2) Chargement existant
    with session_scope() as s:
        repo = UserRepo(s)
        existing = repo.get_by_id(user_id)
        if not existing:
            print("   ❌ Collaborateur introuvable.")
            return None

    # 3) Saisie champs (Enter = garder)
    try:
        new_username = _prompt_keep_or_change("🧑  Nom d’utilisateur", existing.username)
        new_email = _prompt_keep_or_change("📧 Email", existing.email)

        # Validation email
        if new_email != existing.email:
            _validate_email(new_email)

        new_role = _choose_role(existing.role)
        new_is_active = _yes_no("Activer le compte ?", existing.is_active)
        new_is_staff = _yes_no("Flag staff ?", existing.is_staff)
        new_is_superuser = _yes_no("Flag superuser ?", existing.is_superuser)

        # Password (optionnel)
        change_pwd = _yes_no("Changer le mot de passe ?", False)
        if change_pwd:
            while True:
                pwd1 = getpass("   🔒 Nouveau mot de passe : ").strip()
                if pwd1.lower() == "retour":
                    raise KeyboardInterrupt
                if len(pwd1) < 8:
                    print("   ❌ Mot de passe trop court (8+ caractères).")
                    continue
                pwd2 = getpass("   🔒 Confirmation : ").strip()
                if pwd1 != pwd2:
                    print("   ❌ Les mots de passe ne correspondent pas.")
                    continue
                break
        else:
            pwd1 = None

    except KeyboardInterrupt:
        print("   ❌ Modification annulée.")
        return None

    # 4) Unicité (si changements)
    with session_scope() as s:
        repo = UserRepo(s)

        if new_username != existing.username:
            dup = repo.get_by_username(new_username)
            if dup and dup.id != existing.id:
                print("   ❌ Ce nom d’utilisateur est déjà pris.")
                return None

        if new_email != existing.email:
            dup = repo.get_by_email(new_email)
            if dup and dup.id != existing.id:
                print("   ❌ Cet email est déjà utilisé.")
                return None

    # 5) Récap
    print("\n" + "-" * 50)
    print("📋  RÉCAPITULATIF".center(50))
    print("-" * 50)
    print(f"   🆔 ID         : {existing.id}")
    print(f"   🧑  Username  : {existing.username} → {new_username}")
    print(f"   📧 Email     : {existing.email} → {new_email}")
    print(f"   🔐 Rôle      : {existing.role.name} → {new_role.name}")
    print(f"   ✅ Actif     : {'Oui' if existing.is_active else 'Non'} → {'Oui' if new_is_active else 'Non'}")
    print(f"   🛠  Staff     : {'Oui' if existing.is_staff else 'Non'} → {'Oui' if new_is_staff else 'Non'}")
    print(f"   👑 Superuser : {'Oui' if existing.is_superuser else 'Non'} → {'Oui' if new_is_superuser else 'Non'}")
    print(f"   🔒 Mot de passe : {'(inchangé)' if not pwd1 else '(sera mis à jour)'}")
    print("-" * 50)

    if input("   Confirmer la modification ? (o/N) : ").strip().lower() != "o":
        print("   ❌ Modification annulée.")
        return None

    # 6) Construction entité modifiée (copie + mutations)
    u = User(
        id=existing.id,
        username=new_username,
        email=new_email,
        role=new_role,
        is_active=new_is_active,
        is_staff=new_is_staff,
        is_superuser=new_is_superuser,
        last_login=existing.last_login,
        date_joined=existing.date_joined,
        created_at=existing.created_at,
    )

    if pwd1:
        _set_password_on_user(u, pwd1)

    # 7) Appel use-case (autorisation + persistance)
    try:
        updated = service.update(u, auth=auth)
        if not updated:
            print("❌ Aucune mise à jour (utilisateur introuvable ou non modifié).")
            return None
        print(f"✅ Collaborateur #{updated.id} mis à jour ({updated.username} — {updated.role.name}).")
        return updated
    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
    except Exception as e:
        print(f"❌ Erreur lors de la modification : {e}")

    return None