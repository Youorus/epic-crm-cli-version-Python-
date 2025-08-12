# cli/services/contracts/update_contract_form.py
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional

from models.contract import Contract
from security.authorization import AuthContext, AuthzError, Role
from services.usecases.contract_crud import ContractService
from services.crud.client_repo import ClientRepo
from services.db_session import session_scope


# ─────────────────────────────────────────────────────────
# Helpers parsing / validation (alignés avec create_contract_form)
# ─────────────────────────────────────────────────────────
def _parse_money(raw: str) -> Decimal:
    """
    Accepte : '1 234,50', '1234.50', '1 234,50 €', '1234', etc.
    Retourne un Decimal(2 décimales) ou lève ValueError.
    """
    if raw is None:
        raise ValueError("Montant requis.")
    s = str(raw).strip()
    if not s:
        raise ValueError("Montant requis.")
    for ch in ("€", " ", "\u00A0", "\u202F"):
        s = s.replace(ch, "")
    s = s.replace(",", ".")
    try:
        d = Decimal(s)
    except (InvalidOperation, ValueError):
        raise ValueError("Montant invalide.")
    if d < 0:
        raise ValueError("Le montant ne peut pas être négatif.")
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _parse_yes_no_optional(raw: str, *, default: bool) -> bool:
    s = (raw or "").strip().lower()
    if s == "":
        return default
    if s in ("o", "oui", "y", "yes", "1", "true", "vrai"):
        return True
    if s in ("n", "non", "no", "0", "false", "faux"):
        return False
    raise ValueError("Répondez par oui/oui (o) ou non (n), ou laissez vide pour conserver la valeur.")


def _input_int_optional(prompt: str) -> Optional[int]:
    """
    Lit un entier ou vide (→ None).
    """
    s = input(prompt).strip()
    if s == "":
        return None
    if not s.isdigit():
        raise ValueError("La valeur doit être un entier.")
    return int(s)


def _input_money_optional(prompt: str) -> Optional[Decimal]:
    s = input(prompt).strip()
    if s == "":
        return None
    return _parse_money(s)


# ─────────────────────────────────────────────────────────
# Formulaire principal de MISE À JOUR
# ─────────────────────────────────────────────────────────
def update_contract_form(
    *,
    service: ContractService,
    auth: AuthContext,
) -> Optional[Contract]:
    """
    Met à jour un contrat existant (ID demandé).
    - Permet de modifier : client_id, sales_contact_id, total_amount, amount_due, is_signed.
    - Champs laissés vides = inchangés.
    - Valide : montants >= 0 et amount_due <= total_amount.
    - Autorisation via ContractService.update (GESTION ou commercial propriétaire, selon tes règles).
    """
    print("\n" + "=" * 50)
    print("✏️  MODIFICATION D’UN CONTRAT".center(50))
    print("=" * 50)
    print("(Tapez 'retour' à tout moment pour annuler.)\n")

    # 0) ID du contrat
    s = input("   🔢 ID du contrat à modifier : ").strip()
    if s.lower() == "retour":
        print("   ❌ Opération annulée.")
        return None
    if not s.isdigit():
        print("   ❌ L’ID doit être un entier.")
        return None
    contract_id = int(s)

    # 1) Charger l'existant (via service pour bénéficier des règles d'accès)
    try:
        existing = service.get(contract_id, auth=auth)
    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")
        return None

    if not existing:
        print("   ❌ Contrat introuvable.")
        return None

    # 2) Affichage résumé
    print("\n" + "-" * 50)
    print("📋  CONTRAT ACTUEL".center(50))
    print("-" * 50)
    print(f"   🆔 ID              : {existing.id}")
    print(f"   🔗 Client ID       : {existing.client_id}")
    print(f"   🧑‍💼 SalesContactID : {existing.sales_contact_id or '—'}")
    print(f"   💼 Total           : {existing.total_amount:.2f} €")
    print(f"   💳 Dû              : {existing.amount_due:.2f} €")
    print(f"   ✍️  Signé           : {'Oui' if existing.is_signed else 'Non'}")

    print("\n--- Laissez vide pour conserver la valeur actuelle ---")

    # 3) Saisie des modifications
    # 3.1) Client (optionnel) + vérification existence si modifié
    try:
        new_client_id = _input_int_optional("   🔗 Nouveau client ID (vide = inchangé) : ")
        if new_client_id is not None:
            with session_scope() as sess:
                if not ClientRepo(sess).get(new_client_id):
                    print("   ❌ Client introuvable.")
                    return None
    except ValueError as e:
        print(f"   ❌ {e}")
        return None

    # 3.2) Sales contact (optionnel)
    try:
        new_sales_contact_id = _input_int_optional("   🧑‍💼 Nouveau SalesContactID (vide = inchangé/None) : ")
    except ValueError as e:
        print(f"   ❌ {e}")
        return None

    # 3.3) Montants (optionnels)
    try:
        new_total = _input_money_optional("   💼 Nouveau total (€) (vide = inchangé) : ")
        new_due = _input_money_optional("   💳 Nouveau dû (€)    (vide = inchangé) : ")
    except ValueError as e:
        print(f"   ❌ {e}")
        return None

    # 3.4) Signé (optionnel)
    try:
        s = input("   ✍️  Contrat signé ? (o/n, vide = inchangé) : ").strip()
        if s.lower() == "retour":
            print("   ❌ Opération annulée.")
            return None
        new_signed = _parse_yes_no_optional(s, default=existing.is_signed)
    except ValueError as e:
        print(f"   ❌ {e}")
        return None

    # 4) Construire l’entité à mettre à jour (copie + modifications)
    updated = Contract(
        id=existing.id,
        client_id=new_client_id if new_client_id is not None else existing.client_id,
        sales_contact_id=new_sales_contact_id if new_sales_contact_id is not None else existing.sales_contact_id,
        total_amount=new_total if new_total is not None else existing.total_amount,
        amount_due=new_due if new_due is not None else existing.amount_due,
        is_signed=new_signed,
        created_at=existing.created_at,   # conservé
        updated_at=None,                  # laisser la DB/mapper gérer
    )

    # 5) Validation métier locale (due ≤ total)
    if updated.amount_due > updated.total_amount:
        print("   ❌ Le montant dû ne peut pas dépasser le montant total.")
        return None

    # 6) Récap
    print("\n" + "-" * 50)
    print("📋  MODIFICATIONS".center(50))
    print("-" * 50)
    print(f"   🔗 Client ID       : {existing.client_id} → {updated.client_id}")
    print(f"   🧑‍💼 SalesContactID : {existing.sales_contact_id or '—'} → {updated.sales_contact_id or '—'}")
    print(f"   💼 Total           : {existing.total_amount:.2f} € → {updated.total_amount:.2f} €")
    print(f"   💳 Dû              : {existing.amount_due:.2f} € → {updated.amount_due:.2f} €")
    print(f"   ✍️  Signé           : {'Oui' if existing.is_signed else 'Non'} → {'Oui' if updated.is_signed else 'Non'}")
    print("-" * 50)

    confirm = input("   Confirmer la modification ? (o/N) : ").strip().lower()
    if confirm != "o":
        print("   ❌ Modification annulée.")
        return None

    # 7) Appel use-case (autorisation + persistance)
    try:
        saved = service.update(updated, auth=auth)
        if not saved:
            print("❌ Impossible de mettre à jour (introuvable ou non autorisé).")
            return None

        print(f"✅ Contrat #{saved.id} mis à jour avec succès.")
        return saved

    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour : {e}")

    return None