"""Module utilitaire fournissant des fonctions pour la validation des données, la saisie utilisateur et la gestion sécurisée des mots de passe."""

import os
import re
import hashlib
from enums.user_role import UserRole
from models.users import User
from typing import Optional

# ─────────────────────────────────────────────────────────
# Helpers validations / sécurité
# ─────────────────────────────────────────────────────────

# Expression régulière pour valider le format d'une adresse email.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(email: str) -> None:
    """
    Valide le format d'une adresse email.

    Args:
        email (str): L'adresse email à valider.

    Raises:
        ValueError: Si l'adresse email est vide ou ne correspond pas au format attendu.
    """
    if not email or not _EMAIL_RE.match(email):
        raise ValueError("Adresse email invalide.")


def _choose_role() -> UserRole:
    """
    Propose à l'utilisateur de choisir un rôle parmi les rôles définis dans UserRole.

    Returns:
        UserRole: Le rôle sélectionné par l'utilisateur.

    Raises:
        KeyboardInterrupt: Si l'utilisateur entre 'retour' pour annuler la sélection.
    """
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
    """
    Demande une réponse oui/non à l'utilisateur avec une valeur par défaut.

    Args:
        prompt (str): Le message affiché à l'utilisateur.
        default (bool, optional): La valeur par défaut si l'utilisateur ne saisit rien. Par défaut True.

    Returns:
        bool: True pour oui, False pour non.
    """
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


# Fonction pour générer un hash sécurisé du mot de passe avec un sel aléatoire.
def _hash_password(password: str) -> tuple[bytes, bytes]:
    """
    Génère un hash sécurisé du mot de passe en utilisant l'algorithme scrypt.

    Args:
        password (str): Le mot de passe en clair.

    Returns:
        tuple[bytes, bytes]: Un tuple contenant le sel (salt) et le hash dérivé (dk).
    """
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return salt, dk


def _set_password_on_user(u: User, password: str) -> None:
    """
    Définit le mot de passe sur un objet utilisateur. Utilise la méthode set_password si disponible,
    sinon stocke le sel et le hash en attributs privés.

    Args:
        u (User): L'objet utilisateur sur lequel définir le mot de passe.
        password (str): Le mot de passe en clair.
    """
    if hasattr(u, "set_password") and callable(getattr(u, "set_password")):
        u.set_password(password)  # type: ignore[attr-defined]
        return
    # fallback privé si le domaine ne fournit pas set_password
    salt, h = _hash_password(password)
    setattr(u, "_password_salt", salt)
    setattr(u, "_password_hash", h)


def _input_int(prompt: str) -> Optional[int]:
    """
    Demande à l'utilisateur de saisir un entier via l'entrée standard.

    Args:
        prompt (str): Le message affiché à l'utilisateur.

    Returns:
        Optional[int]: L'entier saisi, ou None si l'utilisateur tape 'retour'.

    Prints:
        Message d'erreur si la saisie n'est pas un entier valide.
    """
    s = input(prompt).strip()
    if s.lower() == "retour":
        return None
    if not s.isdigit():
        print("   ❌ L’ID doit être un entier.")
        return _input_int(prompt)
    return int(s)


def _prompt_keep_or_change(prompt: str, current: str) -> str:
    """
    Affiche une valeur actuelle et permet à l'utilisateur de la modifier.
    Si l'entrée est vide, la valeur courante est conservée.

    Args:
        prompt (str): Le message affiché à l'utilisateur.
        current (str): La valeur actuelle affichée entre crochets.

    Returns:
        str: La nouvelle valeur saisie ou la valeur actuelle si entrée vide.

    Raises:
        KeyboardInterrupt: Si l'utilisateur entre 'retour' pour annuler.
    """
    s = input(f"   {prompt} [{current}] : ").strip()
    if s.lower() == "retour":
        raise KeyboardInterrupt
    return current if s == "" else s


def _input_id_or_retour(prompt: str) -> Optional[int]:
    """
    Demande à l'utilisateur de saisir un ID entier ou de taper 'retour' pour annuler.

    Args:
        prompt (str): Le message affiché à l'utilisateur.

    Returns:
        Optional[int]: L'ID saisi ou None si l'utilisateur tape 'retour'.

    Prints:
        Message d'erreur si la saisie n'est pas un entier valide.
    """
    s = input(prompt).strip()
    if s.lower() == "retour":
        return None
    if not s.isdigit():
        print("   ❌ L’ID doit être un entier.")
        return _input_id_or_retour(prompt)
    return int(s)