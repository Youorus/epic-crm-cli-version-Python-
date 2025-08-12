from typing import Optional, List, Any
from models.contract import Contract
from datetime import datetime, timezone, timedelta
from datetime import datetime, date
from security.authorization import AuthContext, AuthzError
from services.crud.client_repo import ClientRepo
from services.crud.user_repo import UserRepo
from services.db_session import session_scope
from services.usecases.contract_crud import ContractService
from typing import List, Optional, Any, Dict, Iterable

def _input_int(prompt: str, *, allow_blank: bool = False) -> Optional[int]:
    s = input(prompt).strip()
    if allow_blank and s == "":
        return None
    if not s.isdigit():
        raise ValueError("La valeur doit être un entier.")
    return int(s)


# --- Helpers rôle -------------------------------------------------------------

def _role_name(val) -> str:
    """
    Normalise la représentation du rôle en chaîne :
    - Enum -> .name (ex: Role.SUPPORT -> "SUPPORT")
    - "UserRole.SUPPORT" -> "SUPPORT"
    - "SUPPORT" -> "SUPPORT"
    - None/unknown -> ""
    """
    if val is None:
        return ""
    # Enum (Role, UserRole, etc.) -> utiliser .name si présent
    name = getattr(val, "name", None)
    if isinstance(name, str):
        return name
    # Chaine "UserRole.SUPPORT" ou "Role.SUPPORT" -> récupérer la dernière partie
    s = str(val)
    if "." in s:
        return s.split(".")[-1]
    return s


def _is_support_role(val) -> bool:
    return _role_name(val).upper() == "SUPPORT"


def _is_gestion_role(val) -> bool:
    return _role_name(val).upper() == "GESTION"

# ─────────────────────────────────────────────────────────
# Helpers parsing / saisie
# ─────────────────────────────────────────────────────────
_DT_FORMATS = (
    "%Y-%m-%d %H:%M",      # 2025-08-15 14:30
    "%Y-%m-%dT%H:%M",      # 2025-08-15T14:30
    "%Y-%m-%d %H:%M:%S",   # 2025-08-15 14:30:00
    "%Y-%m-%dT%H:%M:%S",   # 2025-08-15T14:30:00
)

def _parse_dt(s: str) -> datetime:
    s = (s or "").strip()
    for fmt in _DT_FORMATS:
        try:
            # naïf → on l’attache à l’UTC
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    raise ValueError(
        "Date/heure invalide. Formats acceptés : "
        "YYYY-MM-DD HH:MM, YYYY-MM-DDTHH:MM, (optionnel : :SS)."
    )

def _req_str(prompt: str) -> Optional[str]:
    while True:
        s = input(prompt).strip()
        if s.lower() == "retour":
            return None
        if s:
            return s
        print("   ❌ Champ obligatoire.")

def _req_int_pos(prompt: str, min_val: int = 1) -> Optional[int]:
    while True:
        s = input(prompt).strip()
        if s.lower() == "retour":
            return None
        if not s.isdigit():
            print("   ❌ Entrez un entier positif.")
            continue
        val = int(s)
        if val < min_val:
            print(f"   ❌ Valeur minimale : {min_val}.")
            continue
        return val

def _req_dt(prompt: str) -> Optional[datetime]:
    while True:
        s = input(prompt).strip()
        if s.lower() == "retour":
            return None
        try:
            return _parse_dt(s)
        except ValueError as e:
            print(f"   ❌ {e}")

def _confirm(prompt: str = "   Confirmer ? (o/N) : ") -> bool:
    return input(prompt).strip().lower() == "o"


# ─────────────────────────────────────────────────────────
# Sélection du contrat (signé seulement)
# ─────────────────────────────────────────────────────────
def _only_signed(contracts: List[Contract]) -> List[Contract]:
    return [c for c in contracts if bool(getattr(c, "is_signed", False))]

def _fmt_money(val: Any) -> str:
    try:
        # compatible Decimal/int/float/str
        from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
        if val is None:
            d = Decimal("0.00")
        elif isinstance(val, Decimal):
            d = val
        else:
            s = str(val).replace("€", "").replace("\u202f", "").replace(" ", "").replace(",", ".")
            d = Decimal(s)
        d = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        txt = f"{float(d):,.2f}".replace(",", " ").replace(".", ",")
        return f"{txt} €"
    except Exception:
        return str(val)

def _pick_signed_contract(*, contract_service: ContractService, auth: AuthContext) -> Optional[Contract]:
    try:
        all_items = contract_service.list(auth=auth)
    except AuthzError as e:
        print(f"⛔ Accès refusé aux contrats : {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur lors du chargement des contrats : {e}")
        return None

    items = _only_signed(all_items)
    if not items:
        print("ℹ️ Aucun contrat SIGNÉ disponible. Impossible de créer un événement.")
        return None

    print("\n📄 Contrats SIGNÉS disponibles :")
    print("ID   Client_id  Total        Dû")
    print("----------------------------------------")
    for c in items:
        print(
            f"{str(getattr(c, 'id', '')):<4} "
            f"{str(getattr(c, 'client_id', '')):<10} "
            f"{_fmt_money(getattr(c, 'total_amount', 0)):<12} "
            f"{_fmt_money(getattr(c, 'amount_due', 0)):<12}"
        )

    while True:
        s = input("\n   🔗 ID du contrat (ou 'retour') : ").strip()
        if s.lower() == "retour":
            return None
        if not s.isdigit():
            print("   ❌ L’ID doit être un entier.")
            continue
        cid = int(s)
        found = next((c for c in items if getattr(c, "id", None) == cid), None)
        if not found:
            print("   ❌ Contrat introuvable dans la liste des contrats signés.")
            continue
        return found

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


_ACCEPTED = "YYYY-MM-DD HH:MM[,SS] ou YYYY-MM-DDTHH:MM[,SS]"


def _parse_dt(raw: str) -> datetime:
    s = (raw or "").strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Date/heure invalide. Formats acceptés : {_ACCEPTED}.")


def _input_int(prompt: str, allow_blank: bool = False) -> Optional[int]:
    s = input(prompt).strip()
    if allow_blank and s == "":
        return None
    if not s.isdigit():
        raise ValueError("La valeur doit être un entier.")
    return int(s)
