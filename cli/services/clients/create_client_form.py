from __future__ import annotations

from typing import Optional

from cli.services.clients.utils import _req_str, _opt_str, _confirm
from models.clients import Client
from security.authorization import AuthContext, AuthzError, Role
from services.usecases.client_crud import ClientService



# -------- Formulaire principal --------
def create_client_form(*, service: ClientService, auth: AuthContext) -> Optional[Client]:
    """
    Crée un client en respectant les règles métier :
      - GESTION : peut créer pour n'importe quel commercial (ou aucun)
      - COMMERCIAL : création autorisée et auto-assignation au commercial connecté
    Retourne le Client créé ou None si annulé.
    """
    print("\n" + "=" * 50)
    print("📝  CRÉATION D’UN CLIENT".center(50))
    print("=" * 50)
    print("(Tapez 'retour' à tout moment pour annuler.)\n")

    # Saisie des champs
    full_name = _req_str("   👤 Nom complet : ")
    if full_name is None:
        print("   ❌ Création annulée.")
        return None

    email = _req_str("   📧 Email       : ")
    if email is None:
        print("   ❌ Création annulée.")
        return None

    phone = _req_str("   📞 Téléphone   : ")
    if phone is None:
        print("   ❌ Création annulée.")
        return None

    company_name = _req_str("   🏢 Entreprise  : ")
    if company_name is None:
        print("   ❌ Création annulée.")
        return None

    # Gestion du sales_contact_id
    sales_contact_id: Optional[int] = None
    if auth.role == Role.COMMERCIAL:
        # auto-assignation au commercial connecté
        sales_contact_id = auth.user_id
    else:
        # Rôle GESTION : possibilité de spécifier un SC explicite (optionnel)
        raw_sc = _opt_str("   👔 ID commercial (laisser vide si aucun) : ")
        if raw_sc is None:
            print("   ❌ Création annulée.")
            return None
        if raw_sc:
            if raw_sc.isdigit():
                sales_contact_id = int(raw_sc)
            else:
                print("   ⚠️  ID commercial ignoré (doit être un entier).")

    # Récap
    print("\n" + "-" * 50)
    print("📋  RÉCAPITULATIF CLIENT".center(50))
    print("-" * 50)
    print(f"   👤 Nom complet : {full_name}")
    print(f"   📧 Email       : {email}")
    print(f"   📞 Téléphone   : {phone}")
    print(f"   🏢 Entreprise  : {company_name}")
    print(f"   👔 SalesContact: {sales_contact_id if sales_contact_id else '—'}")
    print("-" * 50)

    if not _confirm("   Confirmer la création ? (o/N) : "):
        print("   ❌ Création annulée.")
        return None

    # Construction de l'entité domaine
    client = Client.create(
        full_name=full_name,
        email=email,
        phone=phone,
        company_name=company_name,
        sales_contact_id=sales_contact_id,
    )

    # Persistance via use-case (avec contrôles d'autorisations)
    try:
        created = service.create(client, auth=auth)
        print(f"✅ Client #{created.id} créé avec succès.")
        return created
    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
    except Exception as e:
        print(f"❌ Erreur lors de la création : {e}")

    return None