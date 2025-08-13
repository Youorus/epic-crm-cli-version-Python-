# cli/services/events/assign_support_form.py
from __future__ import annotations

from typing import Optional

from models.event import Event
from security.authorization import AuthContext, AuthzError, Role, can_read_users
from services.usecases.event_crud import EventService
from services.usecases.user_crud import UserService

# --- Helpers locaux de rôles -------------------------------------------------


def _role_name(r) -> str:
    """
    Retourne un nom de rôle lisible et robuste quel que soit le type :
    - Enum (Role / UserRole) -> r.value
    - str -> r (inchangé)
    - None -> "—"
    """
    if r is None:
        return "—"
    # Enums Role / UserRole ont un .value ; sinon str(r)
    return getattr(r, "value", str(r))

def _is_gestion_role(r) -> bool:
    """
    True si r vaut 'GESTION' (accepte Role.GESTION, UserRole.GESTION, 'GESTION', etc.).
    """
    name = _role_name(r)
    return isinstance(name, str) and name.upper() == "GESTION"

def _is_support_role(r) -> bool:
    """
    True si r vaut 'SUPPORT' (accepte Role.SUPPORT, UserRole.SUPPORT, 'SUPPORT', etc.).
    """
    name = _role_name(r)
    return isinstance(name, str) and name.upper() == "SUPPORT"



# --- Formulaire ---------------------------------------------------------------

def assign_support_to_event_form(
    *,
    event_service: EventService,
    user_service: UserService,
    auth: AuthContext,
) -> Optional[Event]:
    """
    Assigne (ou ré-assigne) un utilisateur de rôle SUPPORT à un événement.
    - Par défaut réservé à GESTION (adapter si besoin).
    - Valide l’existence de l’événement et du support.
    - Persiste via EventService.update(...).
    """
    print("\n" + "=" * 50)
    print("👷  ASSIGNATION D’UN SUPPORT À UN ÉVÉNEMENT".center(50))
    print("=" * 50)
    print("(Tapez 'retour' à tout moment pour annuler.)\n")

    # Autorisation locale
    if not _is_gestion_role(getattr(auth, "role", None)):
        print("⛔ Accès refusé : seule la GESTION peut assigner un support.")
        return None

    # ID évènement
    while True:
        s = input("   🔢 ID de l’événement : ").strip()
        if s.lower() == "retour":
            print("   ❌ Opération annulée.")
            return None
        try:
            if not s.isdigit():
                raise ValueError("L’ID doit être un entier.")
            event_id = int(s)
            break
        except ValueError as e:
            print(f"   ❌ {e}")

    # Récup événement
    try:
        ev = event_service.get(event_id, auth=auth)
    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur lors du chargement de l’événement : {e}")
        return None

    if not ev:
        print("❌ Événement introuvable.")
        return None

    curr_support_txt = str(ev.support_contact_id) if ev.support_contact_id else "—"
    print(f"   ℹ️ Événement: #{ev.id} — « {ev.event_name} »")
    print(f"   📍 Lieu     : {ev.location}")
    print(f"   👥 Participants : {ev.attendees}")
    print(f"   👷 Support actuel : {curr_support_txt}\n")

    # ID support
    print("   Saisissez l’ID d’un collaborateur ayant le rôle SUPPORT.")
    print("   (laisser vide pour annuler)")
    s = input("   👷 ID du support : ").strip()
    if s.lower() == "retour" or s == "":
        print("   ❌ Opération annulée.")
        return None
    if not s.isdigit():
        print("   ❌ L’ID doit être un entier.")
        return None
    support_id = int(s)

    # Validation droit de lecture des user + existence + rôle SUPPORT
    try:
        if not can_read_users(auth):
            print("⛔ Accès refusé pour lire les utilisateurs.")
            return None

        u = user_service.get(support_id, auth=auth)
    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur lors de la vérification du support : {e}")
        return None

    if not u:
        print("❌ Collaborateur introuvable.")
        return None
    if not _is_support_role(getattr(u, "role", None)):
        # Affiche ce qu'on a trouvé pour aider au debug
        print(f"❌ Le collaborateur choisi n’a pas le rôle SUPPORT (rôle trouvé : {_role_name(getattr(u, 'role', None))}).")
        return None

    # Récap
    print("\n" + "-" * 50)
    print("📋  RÉCAPITULATIF".center(50))
    print("-" * 50)
    print(f"   🆔 Événement       : #{ev.id} — « {ev.event_name} »")
    print(f"   👷 Nouveau support : #{support_id}")
    print("-" * 50)
    confirm = input("   Confirmer l’assignation ? (o/N) : ").strip().lower()
    if confirm != "o":
        print("   ❌ Assignation annulée.")
        return None

    # Construction d’un Event mis à jour
    updated = Event(
        id=ev.id,
        contract_id=ev.contract_id,
        client_id=ev.client_id,
        support_contact_id=support_id,
        event_name=ev.event_name,
        event_start=ev.event_start,
        event_end=ev.event_end,
        location=ev.location,
        attendees=ev.attendees,
        notes=ev.notes,
        created_at=ev.created_at,
    )

    # Persistance
    try:
        saved = event_service.update(updated, auth=auth)
        if not saved:
            print("❌ Mise à jour impossible (événement introuvable).")
            return None
        print(f"✅ Support #{support_id} assigné à l’événement #{ev.id}.")
        return saved
    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
    except Exception as e:
        print(f"❌ Erreur lors de l’assignation : {e}")

    return None