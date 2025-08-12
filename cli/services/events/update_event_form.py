# cli/services/events/update_event_form.py
from __future__ import annotations

from typing import Optional
from datetime import datetime
from security.authorization import AuthContext, AuthzError, Role
from services.usecases.event_crud import EventService


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


def update_event_form_support(
    *,
    service: EventService,
    auth: AuthContext,
) -> Optional[None]:
    """
    Formulaire de mise à jour d’un événement pour un utilisateur SUPPORT.
    Le backend (EventService.can_update_event) vérifiera que l’événement est bien assigné à ce support.
    """
    if auth.role not in (Role.SUPPORT, Role.GESTION):
        print("⛔ Réservé aux rôles SUPPORT / GESTION.")
        return None

    print("\n" + "=" * 50)
    print("🛠️  MISE À JOUR D’UN ÉVÉNEMENT".center(50))
    print("=" * 50)
    print("(Tapez 'retour' à tout moment pour annuler.)\n")

    # 1) ID
    while True:
        s = input("   🔢 ID de l’événement : ").strip()
        if s.lower() == "retour":
            print("   ❌ Annulé.")
            return None
        try:
            if not s.isdigit():
                raise ValueError("L’ID doit être un entier.")
            event_id = int(s)
            break
        except ValueError as e:
            print(f"   ❌ {e}")

    # 2) Charger l’événement existant
    try:
        existing = service.get(event_id, auth=auth)
        if not existing:
            print("   ❌ Événement introuvable.")
            return None
    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")
        return None

    print("\n--------------------------------------------------")
    print("                 📋  ACTUEL                       ")
    print("--------------------------------------------------")
    print(f"   🆔 ID          : {existing.id}")
    print(f"   🏷️  Nom         : {existing.event_name}")
    print(f"   🕒 Début       : {existing.event_start}")
    print(f"   🕒 Fin         : {existing.event_end}")
    print(f"   📍 Lieu        : {existing.location}")
    print(f"   👥 Participants: {existing.attendees}")
    print(f"   📝 Notes       : {existing.notes}")
    print("--------------------------------------------------")

    # 3) Collecte des nouvelles valeurs (toutes optionnelles)
    name = input("   Nouveau nom (laisser vide pour conserver) : ").strip()
    start_raw = input(f"   Nouveau début ({_ACCEPTED}) (laisser vide) : ").strip()
    end_raw = input(f"   Nouvelle fin   ({_ACCEPTED}) (laisser vide) : ").strip()
    location = input("   Nouveau lieu (laisser vide) : ").strip()
    attendees_raw = input("   Nouveaux participants (entier, laisser vide) : ").strip()
    notes = input("   Nouvelles notes (laisser vide) : ").strip()

    # 4) Appliquer les changements sur l’entité
    try:
        if name:
            existing.rename(name)
        if start_raw:
            new_start = _parse_dt(start_raw)
        else:
            new_start = existing.event_start
        if end_raw:
            new_end = _parse_dt(end_raw)
        else:
            new_end = existing.event_end
        if start_raw or end_raw:
            existing.move(new_start=new_start, new_end=new_end)
        if location:
            existing.change_location(location)
        if attendees_raw:
            if not attendees_raw.isdigit():
                raise ValueError("Participants doit être un entier positif.")
            existing.set_attendees(int(attendees_raw))
        if notes:
            existing.update_notes(notes)
    except ValueError as e:
        print(f"   ❌ {e}")
        return None

    # 5) Confirmer et persister
    confirm = input("   Confirmer la mise à jour ? (o/N) : ").strip().lower()
    if confirm != "o":
        print("   ❌ Annulé.")
        return None

    try:
        updated = service.update(existing, auth=auth)
        if not updated:
            print("❌ Échec de la mise à jour (introuvable ou non autorisé).")
            return None
        print("✅ Événement mis à jour.")
    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
    except Exception as e:
        print(f"❌ Erreur lors de l’enregistrement : {e}")
    return None