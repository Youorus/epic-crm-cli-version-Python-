# cli/services/events/list_events.py
from __future__ import annotations

from typing import List, Optional, Any, Dict, Iterable
from datetime import datetime, date

from security.authorization import AuthContext, AuthzError
from services.usecases.event_crud import EventService

# Résolution des noms (optionnelle, si les repos existent)
try:
    from services.db_session import session_scope
    from services.crud.client_repo import ClientRepo
    from services.crud.user_repo import UserRepo
except Exception:  # pragma: no cover - si pas de repos disponibles
    session_scope = None  # type: ignore
    ClientRepo = None     # type: ignore
    UserRepo = None       # type: ignore


# ─────────────────────────────────────────────────────────
# Helpers d'affichage locaux (autonomes)
# ─────────────────────────────────────────────────────────
def _clip(val: Any, width: int) -> str:
    """Coupe proprement une chaîne pour tenir dans 'width' colonnes."""
    s = "" if val is None else str(val)
    return (s[: width - 1] + "…") if len(s) > width else s


def _fmt_dt(dt: Any) -> str:
    """Affiche 'YYYY-MM-DD HH:MM' si datetime, 'YYYY-MM-DD' si date, sinon str/—."""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M")
    if isinstance(dt, date):
        return dt.strftime("%Y-%m-%d")
    return str(dt) if dt is not None else "—"


def _build_maps(events: Iterable[Any]) -> tuple[Dict[int, str], Dict[int, str]]:
    """
    Construit 2 maps:
      - client_names[client_id] = client.full_name (fallback "Client #id")
      - user_names[user_id]     = user.username   (fallback "User #id")
    Fonctionne seulement si les repos sont dispo; sinon, renvoie des maps vides.
    """
    client_names: Dict[int, str] = {}
    user_names: Dict[int, str] = {}

    if not (session_scope and ClientRepo and UserRepo):
        return client_names, user_names

    client_ids = {int(e.client_id) for e in events if getattr(e, "client_id", None)}
    user_ids = {int(e.support_contact_id) for e in events if getattr(e, "support_contact_id", None)}

    if not client_ids and not user_ids:
        return client_names, user_names

    with session_scope() as s:
        if client_ids:
            crepo = ClientRepo(s)
            for cid in client_ids:
                c = crepo.get(cid)
                if c:
                    client_names[cid] = getattr(c, "full_name", None) or f"Client #{cid}"
        if user_ids:
            urepo = UserRepo(s)
            for uid in user_ids:
                u = urepo.get(uid)
                if u:
                    user_names[uid] = getattr(u, "username", None) or f"User #{uid}"

    return client_names, user_names


# ─────────────────────────────────────────────────────────
# Service CLI : liste des événements
# ─────────────────────────────────────────────────────────
def list_events(
    *,
    service: EventService,
    auth: AuthContext,
    display: bool = True,
    as_table: bool = True,
    support_isnull: Optional[bool] = None,     # True -> sans support ; False -> avec support
    support_only_mine: bool = False,           # True -> uniquement ceux assignés à auth.user_id
    support_contact_id: Optional[int] = None,  # filtre explicite par support
) -> List:
    """
    Liste les événements via le use-case Python (pas d'API REST).

    Paramètres
    ----------
    service : EventService
        Use-case métier (accès repo + règles d'autorisation).
    auth : AuthContext
        Contexte d'authentification/autorisation courant.
    display : bool
        Si True, affiche la liste dans la console.
    as_table : bool
        Si True, format tableau; sinon, format détaillé.
    support_isnull : Optional[bool]
        - True  -> ne garder que les événements SANS support
        - False -> ne garder que les événements AVEC support
        - None  -> ne filtre pas sur ce critère
    support_only_mine : bool
        Si True, ne garder que ceux où support_contact_id == auth.user_id
    support_contact_id : Optional[int]
        Filtre explicite par id de support.

    Retour
    ------
    List[Event]
    """
    try:
        items = service.list(auth=auth)
    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
        return []
    except Exception as e:
        print(f"❌ Erreur inattendue lors du listing des événements : {e}")
        return []

    # Filtres CLI optionnels
    if support_isnull is True:
        items = [e for e in items if getattr(e, "support_contact_id", None) is None]
    elif support_isnull is False:
        items = [e for e in items if getattr(e, "support_contact_id", None) is not None]

    if support_only_mine and getattr(auth, "user_id", None) is not None:
        uid = int(auth.user_id)  # type: ignore[arg-type]
        items = [e for e in items if getattr(e, "support_contact_id", None) == uid]

    if support_contact_id is not None:
        items = [e for e in items if getattr(e, "support_contact_id", None) == support_contact_id]

    if not items:
        if display:
            print("🔍 Aucun événement trouvé.")
        return items

    if not display:
        return items

    # Résolution des libellés (client/support)
    client_names, user_names = _build_maps(items)

    # ─────────────────────────────────────────────────────────
    # Affichage tableau
    # ─────────────────────────────────────────────────────────
    if as_table:
        W_ID, W_CLIENT, W_SUPPORT, W_NAME, W_START, W_END, W_LOC, W_ATT, W_CREATED = 5, 22, 16, 24, 16, 16, 20, 6, 16

        header = (
            f"{'ID':<{W_ID}} "
            f"{'Client':<{W_CLIENT}} "
            f"{'Support':<{W_SUPPORT}} "
            f"{'Nom':<{W_NAME}} "
            f"{'Début':<{W_START}} "
            f"{'Fin':<{W_END}} "
            f"{'Lieu':<{W_LOC}} "
            f"{'👥':>{W_ATT}} "
            f"{'Créé le':<{W_CREATED}}"
        )

        print("\n📅 === LISTE DES ÉVÉNEMENTS ===")
        print(header)
        print("-" * len(header))

        for e in items:
            cid = getattr(e, "client_id", None)
            scid = getattr(e, "support_contact_id", None)

            client_label = client_names.get(cid, f"Client #{cid}" if cid else "—")
            support_label = (
                user_names.get(scid, f"User #{scid}" if scid else "—")
                if scid is not None else "—"
            )

            row = (
                f"{str(getattr(e, 'id', '')):<{W_ID}} "
                f"{_clip(client_label, W_CLIENT):<{W_CLIENT}} "
                f"{_clip(support_label, W_SUPPORT):<{W_SUPPORT}} "
                f"{_clip(getattr(e, 'event_name', ''), W_NAME):<{W_NAME}} "
                f"{_clip(_fmt_dt(getattr(e, 'event_start', None)), W_START):<{W_START}} "
                f"{_clip(_fmt_dt(getattr(e, 'event_end', None)), W_END):<{W_END}} "
                f"{_clip(getattr(e, 'location', ''), W_LOC):<{W_LOC}} "
                f"{str(getattr(e, 'attendees', '')):>{W_ATT}} "
                f"{_clip(_fmt_dt(getattr(e, 'created_at', None)), W_CREATED):<{W_CREATED}}"
            )
            print(row)

        return items

    # ─────────────────────────────────────────────────────────
    # Affichage détaillé
    # ─────────────────────────────────────────────────────────
    print("\n📅 === LISTE DES ÉVÉNEMENTS (détails) ===")
    for e in items:
        cid = getattr(e, "client_id", None)
        scid = getattr(e, "support_contact_id", None)

        client_label = client_names.get(cid, f"Client #{cid}" if cid else "—")
        support_label = user_names.get(scid, f"User #{scid}" if scid else "—") if scid else "—"

        print("\n" + "-" * 60)
        print(f"🆔 ID           : {getattr(e, 'id', '')}")
        print(f"👤 Client       : {client_label}")
        print(f"🧑‍💼 Support     : {support_label}")
        print(f"📛 Nom          : {getattr(e, 'event_name', '')}")
        print(f"🕒 Début        : {_fmt_dt(getattr(e, 'event_start', None))}")
        print(f"🕓 Fin          : {_fmt_dt(getattr(e, 'event_end', None))}")
        print(f"📍 Lieu         : {getattr(e, 'location', '')}")
        print(f"👥 Participants : {getattr(e, 'attendees', '')}")
        print(f"🗒 Notes        : {getattr(e, 'notes', '')}")
        print(f"📅 Créé le      : {_fmt_dt(getattr(e, 'created_at', None))}")

    return items