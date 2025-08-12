# cli/services/clients/list_clients.py
from __future__ import annotations

from typing import List, Optional, Iterable, Any, Dict
from datetime import date, datetime

from cli.services.clients.utils import _clip, _fmt_dt
from models.clients import Client
from security.authorization import AuthContext, AuthzError
from services.usecases.client_crud import ClientService
from services.crud.user_repo import UserRepo
from services.db_session import session_scope


def _filter_search(items: Iterable[Client], q: Optional[str]) -> List[Client]:
    """Filtre basique côté CLI (contient, insensible à la casse) sur quelques champs."""
    if not q:
        return list(items)
    needle = q.casefold()
    out: List[Client] = []
    for c in items:
        hay = " ".join([
            str(getattr(c, "full_name", "")),
            str(getattr(c, "company_name", "")),
            str(getattr(c, "email", "")),
            str(getattr(c, "phone", "")),
        ]).casefold()
        if needle in hay:
            out.append(c)
    return out


def _display_user_name(u: Any) -> str:
    """
    Construit un nom lisible pour un utilisateur.
    Priorité: "Prénom Nom" > username > f"User #{id}".
    """
    if u is None:
        return "—"
    first = (getattr(u, "first_name", "") or "").strip()
    last = (getattr(u, "last_name", "") or "").strip()
    if first or last:
        return f"{first} {last}".strip()
    username = (getattr(u, "username", "") or "").strip()
    if username:
        return username
    uid = getattr(u, "id", None)
    return f"User #{uid}" if uid else "—"


def _load_sales_contact_names() -> Dict[int, str]:
    """
    Charge une fois tous les utilisateurs pour mapper id -> nom affichable.
    Évite une requête par client.
    """
    names: Dict[int, str] = {}
    with session_scope() as s:
        repo = UserRepo(s)
        for u in repo.list():
            names[getattr(u, "id")] = _display_user_name(u)
    return names


# ─────────────────────────────────────────────────────────
# Service principal (utilisé par le menu Gestion/Commercial)
# ─────────────────────────────────────────────────────────
def list_clients(
    service: ClientService,
    auth: AuthContext,
    *,
    search: Optional[str] = None,
    display: bool = True,
    as_table: bool = True,
) -> List[Client]:
    """
    Récupère les clients via ClientService (CRUD Python pur) et peut afficher un tableau.

    - L’autorisation de lecture est gérée par ClientService + security.filter_clients_for().
    - `search` applique un filtre *local* (coté CLI) en plus de la sécurité.
    - Retourne toujours la liste finale (utile pour des traitements enchaînés).
    """
    try:
        items = service.list(auth=auth)  # sécurité + filtrage métier (ex : COMMERCIAL voit ses clients)
    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
        return []

    items = _filter_search(items, search)

    if not items:
        if display:
            print("🔍 Aucun client trouvé.")
        return []

    # Prépare un map id -> nom du commercial
    try:
        sales_contact_names = _load_sales_contact_names()
    except Exception:
        # Si la récupération des users plante, on retombe gracieusement sur l'ID seul
        sales_contact_names = {}

    if not display:
        return items

    # ─────────────────────────────────────────────────────────
    # Affichage
    # ─────────────────────────────────────────────────────────
    if as_table:
        # Largeurs (ajuste si besoin)
        W_ID, W_NAME, W_COMP, W_EMAIL, W_PHONE, W_SALES, W_LAST, W_CREATED = 5, 24, 22, 28, 16, 20, 14, 16

        header = (
            f"{'ID':<{W_ID}} "
            f"{'Nom complet':<{W_NAME}} "
            f"{'Entreprise':<{W_COMP}} "
            f"{'Email':<{W_EMAIL}} "
            f"{'Téléphone':<{W_PHONE}} "
            f"{'Commercial':<{W_SALES}} "
            f"{'Dernier contact':<{W_LAST}} "
            f"{'Créé le':<{W_CREATED}}"
        )

        print("\n📇 === LISTE DES CLIENTS ===")
        print(header)
        print("-" * len(header))

        for c in items:
            sc_id = getattr(c, "sales_contact_id", None)
            sc_name = sales_contact_names.get(sc_id, "—") if sc_id else "—"

            row = (
                f"{str(getattr(c, 'id', '')):<{W_ID}} "
                f"{_clip(getattr(c, 'full_name', ''), W_NAME):<{W_NAME}} "
                f"{_clip(getattr(c, 'company_name', ''), W_COMP):<{W_COMP}} "
                f"{_clip(getattr(c, 'email', ''), W_EMAIL):<{W_EMAIL}} "
                f"{_clip(getattr(c, 'phone', ''), W_PHONE):<{W_PHONE}} "
                f"{_clip(sc_name, W_SALES):<{W_SALES}} "
                f"{_clip(_fmt_dt(getattr(c, 'last_contact', None)), W_LAST):<{W_LAST}} "
                f"{_clip(_fmt_dt(getattr(c, 'created_at', None)), W_CREATED):<{W_CREATED}}"
            )
            print(row)
    else:
        print("\n📇 === LISTE DES CLIENTS ===")
        for c in items:
            sc_id = getattr(c, "sales_contact_id", None)
            sc_name = sales_contact_names.get(sc_id, "—") if sc_id else "—"

            print("\n" + "-" * 60)
            print(f"🆔 ID             : {getattr(c, 'id', '')}")
            print(f"👤 Nom complet    : {getattr(c, 'full_name', '')}")
            print(f"🏢 Entreprise     : {getattr(c, 'company_name', '')}")
            print(f"📧 Email          : {getattr(c, 'email', '')}")
            print(f"📞 Téléphone      : {getattr(c, 'phone', '')}")
            print(f"👔 Commercial     : {sc_name}")
            print(f"📅 Dernier contact: {_fmt_dt(getattr(c, 'last_contact', None))}")
            print(f"🕒 Créé le        : {_fmt_dt(getattr(c, 'created_at', None))}")

    return items