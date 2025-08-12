# cli/services/clients/update_client_form.py
from __future__ import annotations

from typing import Optional
from datetime import date, datetime

from models.clients import Client
from security.authorization import AuthContext, AuthzError, Role
from services.usecases.client_crud import ClientService

from services.db_session import session_scope
from services.crud.client_repo import ClientRepo


def _parse_date_yyyy_mm_dd(raw: str, *, allow_blank: bool = True) -> Optional[date]:
    s = (raw or "").strip()
    if allow_blank and not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Format attendu: YYYY-MM-DD")


def _looks_like_email(s: str) -> bool:
    return "@" in s and "." in s.split("@")[-1]


def _print_card(c: Client) -> None:
    print("\n" + "-" * 50)
    print("📇  CLIENT ACTUEL".center(50))
    print("-" * 50)
    print(f"   🆔 ID             : {c.id}")
    print(f"   👤 Nom complet    : {c.full_name}")
    print(f"   📧 Email          : {c.email}")
    print(f"   📞 Téléphone      : {c.phone}")
    print(f"   🏢 Entreprise     : {c.company_name}")
    print(f"   🗓️  Dernier contact: {c.last_contact or '—'}")
    print(f"   👔 SalesContactID : {c.sales_contact_id or '—'}")


def update_client_form(
    *,
    service: ClientService,
    auth: AuthContext,
) -> Optional[Client]:
    """
    Met à jour un client existant (lecture -> édition champ par champ).
    Règles d’autorisation (GESTION ou COMMERCIAL propriétaire) déléguées à ClientService.update().
    """
    print("\n" + "=" * 50)
    print("✏️   MODIFICATION D’UN CLIENT".center(50))
    print("=" * 50)
    print("(Tapez 'retour' à tout moment pour annuler.)\n")

    # --- 1) Saisie ID ---
    s = input("   🔢 ID du client à modifier : ").strip()
    if s.lower() == "retour":
        print("   ❌ Opération annulée.")
        return None
    if not s.isdigit():
        print("   ❌ L’ID doit être un entier.")
        return None
    client_id = int(s)

    # --- 2) Chargement client (lecture directe via repo pour UX) ---
    with session_scope() as sess:
        repo = ClientRepo(sess)
        current = repo.get(client_id)
    if not current:
        print("   ❌ Client introuvable.")
        return None

    _print_card(current)

    print("\nLaissez vide un champ pour ne PAS le modifier.")
    # --- 3) Champs éditables ---
    full_name = input("   👤 Nom complet    : ").strip() or None
    email     = input("   📧 Email          : ").strip() or None
    phone     = input("   📞 Téléphone      : ").strip() or None
    company   = input("   🏢 Entreprise     : ").strip() or None
    last_c    = input("   🗓️  Dernier contact (YYYY-MM-DD, vide = inchangé) : ").strip()

    last_contact: Optional[date] = None
    try:
        if last_c != "":
            last_contact = _parse_date_yyyy_mm_dd(last_c, allow_blank=False)
    except ValueError as e:
        print(f"   ❌ {e}")
        return None

    # Validation légère
    if email is not None and not _looks_like_email(email):
        print("   ❌ Email invalide.")
        return None

    # Sales contact éditable uniquement par GESTION (optionnel)
    sales_contact_id: Optional[int] = None
    if auth.role is Role.GESTION:
        s = input("   👔 SalesContactID (vide = inchangé) : ").strip()
        if s.lower() == "retour":
            print("   ❌ Opération annulée.")
            return None
        if s:
            if s.isdigit():
                sales_contact_id = int(s)
            else:
                print("   ⚠️  SalesContactID ignoré (doit être un entier).")

    # --- 4) Construit une entité copiée/éditée ---
    edited = Client(
        id=current.id,
        full_name=full_name if full_name is not None else current.full_name,
        email=email if email is not None else current.email,
        phone=phone if phone is not None else current.phone,
        company_name=company if company is not None else current.company_name,
        last_contact=last_contact if last_contact is not None else current.last_contact,
        sales_contact_id=(
            sales_contact_id if sales_contact_id is not None else current.sales_contact_id
        ),
        created_at=current.created_at,
        updated_at=current.updated_at,
    )

    # --- 5) Confirmation ---
    print("\n" + "-" * 50)
    print("📋  RÉCAP MODIFICATION".center(50))
    print("-" * 50)
    print(f"   👤 Nom complet    : {edited.full_name}")
    print(f"   📧 Email          : {edited.email}")
    print(f"   📞 Téléphone      : {edited.phone}")
    print(f"   🏢 Entreprise     : {edited.company_name}")
    print(f"   🗓️  Dernier contact: {edited.last_contact or '—'}")
    print(f"   👔 SalesContactID : {edited.sales_contact_id or '—'}")
    print("-" * 50)

    confirm = input("   Confirmer la mise à jour ? (o/N) : ").strip().lower()
    if confirm != "o":
        print("   ❌ Modification annulée.")
        return None

    # --- 6) Appel use-case (vérifie droits + persiste) ---
    try:
        updated = service.update(edited, auth=auth)
        if not updated:
            print("❌ Mise à jour non effectuée (client introuvable).")
            return None
        print("✅ Client mis à jour.")
        return updated
    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour : {e}")

    return None