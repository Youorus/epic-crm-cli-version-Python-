# cli/services/events/create_event_form.py
from __future__ import annotations


from typing import Optional

from cli.services.events.utils import _confirm, _req_int_pos, _req_str, _req_dt, _pick_signed_contract
from models.event import Event

from security.authorization import AuthContext, Role, AuthzError
from services.usecases.event_crud import EventService
from services.usecases.contract_crud import ContractService




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