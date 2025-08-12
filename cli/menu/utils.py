from sqlalchemy.orm import session

from security.session_state import get_auth


def _current_username() -> str | None:
    """
    Récupère un nom d’utilisateur "joli" pour l’affichage.
    Essaie session.user (API), sinon ne force rien en local.
    """
    if session and getattr(session, "user", None):
        return session.user.get("username")
    return None  # en local, ton login.py affiche déjà le username


def _current_role() -> str | None:
    """
    Détermine le rôle courant à partir de la session API OU du store JWT local.
    - Priorité à session.user (variant API)
    - Sinon, fallback vers get_auth() (variant login local)
    """
    # Variante API : session.user dict
    if session and getattr(session, "user", None):
        return session.user.get("role")

    # Variante locale : JWT stocké en local
    if get_auth:
        auth = get_auth()
        if auth:
            return getattr(auth, "role", None)

    return None