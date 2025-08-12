# cli/services/events/create_event_form.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any

from models.event import Event
from models.contract import Contract
from security.authorization import AuthContext, Role, AuthzError
from services.usecases.event_crud import EventService
from services.usecases.contract_crud import ContractService


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
# Formulaire principal : création d’un événement
# ─────────────────────────────────────────────────────────
def create_event_form(
    *,
    event_service: EventService,
    contract_service: ContractService,
    auth: AuthContext,
) -> Optional[Event]:
    """
    Crée un événement *uniquement* pour un contrat signé.
    - GESTION : peut créer pour n’importe quel contrat signé
    - COMMERCIAL : peut créer si c’est le commercial du contrat (et contrat signé)
    - SUPPORT : non (refus côté EventService.can_create_event)
    """
    print("\n" + "=" * 50)
    print("🎉  CRÉATION D’UN ÉVÉNEMENT".center(50))
    print("=" * 50)
    print("(Tapez 'retour' à tout moment pour annuler.)\n")

    # 1) Sélection du contrat signé
    contract = _pick_signed_contract(contract_service=contract_service, auth=auth)
    if not contract:
        print("   ❌ Création annulée.")
        return None

    client_id = getattr(contract, "client_id", None)
    if not client_id:
        print("   ❌ Contrat invalide : client_id manquant.")
        return None

    # 2) Saisie des champs événement
    name = _req_str("   🏷️  Nom de l’événement : ")
    if name is None:
        print("   ❌ Création annulée.")
        return None

    start_dt = _req_dt("   🕒 Début (YYYY-MM-DD HH:MM) : ")
    if start_dt is None:
        print("   ❌ Création annulée.")
        return None

    end_dt = _req_dt("   🕒 Fin   (YYYY-MM-DD HH:MM) : ")
    if end_dt is None:
        print("   ❌ Création annulée.")
        return None

    if end_dt <= start_dt:
        print("   ❌ La fin doit être postérieure au début.")
        return None

    location = _req_str("   📍 Lieu : ")
    if location is None:
        print("   ❌ Création annulée.")
        return None

    attendees = _req_int_pos("   👥 Participants (>=1) : ", min_val=1)
    if attendees is None:
        print("   ❌ Création annulée.")
        return None

    notes = input("   📝 Notes (optionnel) : ").strip()

    # 3) (Optionnel) Choisir un support au moment de la création
    support_contact_id: Optional[int] = None
    if auth.role == Role.GESTION:
        raw = input("   👷 ID support (laisser vide si aucun) : ").strip()
        if raw.lower() == "retour":
            print("   ❌ Création annulée.")
            return None
        if raw:
            if raw.isdigit():
                support_contact_id = int(raw)
            else:
                print("   ⚠️  ID support ignoré (doit être un entier).")

    # 4) Récapitulatif
    print("\n" + "-" * 50)
    print("📋  RÉCAPITULATIF ÉVÉNEMENT".center(50))
    print("-" * 50)
    print(f"   🔗 Contrat     : {getattr(contract, 'id', '—')}")
    print(f"   👤 Client ID   : {client_id}")
    print(f"   🏷️  Nom          : {name}")
    print(f"   🕒 Début        : {start_dt.isoformat()}")
    print(f"   🕒 Fin          : {end_dt.isoformat()}")
    print(f"   📍 Lieu         : {location}")
    print(f"   👥 Participants : {attendees}")
    print(f"   👷 Support ID   : {support_contact_id if support_contact_id else '—'}")
    print("-" * 50)

    if not _confirm("   Confirmer la création ? (o/N) : "):
        print("   ❌ Création annulée.")
        return None

    # 5) Construction entité et persistance
    event = Event.create(
        contract_id=getattr(contract, "id"),   # type: ignore[arg-type]
        client_id=client_id,                   # type: ignore[arg-type]
        event_name=name,
        event_start=start_dt,
        event_end=end_dt,
        location=location,
        attendees=attendees,
        support_contact_id=support_contact_id,
        notes=notes,
    )

    try:
        created = event_service.create(event, auth=auth)
        print(f"✅ Événement #{created.id} créé avec succès.")
        return created
    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
    except Exception as e:
        print(f"❌ Erreur lors de la création : {e}")

    return None