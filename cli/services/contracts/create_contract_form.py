# cli/forms/contracts/create_contract_form.py
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional
from datetime import datetime, timezone, date

from models.contract import Contract
from security.authorization import AuthContext, AuthzError, Role
from services.usecases.contract_crud import ContractService
from services.crud.client_repo import ClientRepo
from services.db_session import session_scope


# ─────────────────────────────────────────────────────────
# Helpers parsing / validation
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

    # Nettoyage : enlève symbole euro + tous les espaces (classiques & insécables)
    for ch in ("€", " ", "\u00A0", "\u202F"):
        s = s.replace(ch, "")
    s = s.replace(",", ".")  # virgule -> point

    try:
        d = Decimal(s)
    except (InvalidOperation, ValueError):
        raise ValueError("Montant invalide.")

    if d < 0:
        raise ValueError("Le montant ne peut pas être négatif.")

    # 2 décimales
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _parse_yes_no(raw: str) -> bool:
    s = (raw or "").strip().lower()
    if s in ("o", "oui", "y", "yes", "1", "true", "vrai"):
        return True
    if s in ("n", "non", "no", "0", "false", "faux"):
        return False
    raise ValueError("Répondez par oui/oui (o) ou non (n).")


def _input_int(prompt: str, allow_blank: bool = False) -> Optional[int]:
    s = input(prompt).strip()
    if allow_blank and s == "":
        return None
    if not s.isdigit():
        raise ValueError("La valeur doit être un entier.")
    return int(s)


def _as_utc_date(dt: Optional[datetime]) -> date:
    """
    Convertit un datetime (aware/naive/None) en date (YYYY-MM-DD).
    Si None, utilise maintenant (UTC).
    """
    if dt is None:
        return datetime.now(timezone.utc).date()
    if dt.tzinfo is None:
        # Considère naive comme UTC (évite les surprises)
        return dt.replace(tzinfo=timezone.utc).date()
    return dt.astimezone(timezone.utc).date()


# ─────────────────────────────────────────────────────────
# Sélection/validation client
# ─────────────────────────────────────────────────────────
def _pick_client_id() -> int:
    """
    Demande un client_id et vérifie son existence en base.
    Retourne le client_id si OK, lève ValueError sinon.
    """
    with session_scope() as sess:
        repo = ClientRepo(sess)

        while True:
            try:
                cid = _input_int("   🔗 ID du client : ")
            except ValueError as e:
                print(f"   ❌ {e}")
                continue

            client = repo.get(cid) if cid is not None else None
            if not client:
                print("   ❌ Client introuvable. Réessayez.")
                continue

            print(f"   ✅ Client: {client.full_name} — {client.company_name}")
            return cid  # type: ignore[return-value]


# ─────────────────────────────────────────────────────────
# Formulaire principal
# ─────────────────────────────────────────────────────────
def create_contract_form(
    *,
    service: ContractService,
    auth: AuthContext,
) -> Optional[Contract]:
    """
    Formulaire interactif de création de contrat.
    - Valide les champs (montants, borne 0, due ≤ total, bool signé).
    - Vérifie l'existence du client.
    - Applique les règles d'autorisation via ContractService.create (GESTION only).
    - Retourne le Contract créé ou None si annulé/erreur.
    - ⚠️ Met à jour client.last_contact à la date de création du contrat.
    """
    print("\n" + "=" * 50)
    print("📝  CRÉATION D’UN CONTRAT".center(50))
    print("=" * 50)
    print("(Tapez 'retour' à tout moment pour annuler.)\n")

    # Règle métier (défense côté CLI) : création réservée à GESTION
    if hasattr(auth, "role") and auth.role != Role.GESTION:
        print("⛔ Accès refusé : seule la GESTION peut créer un contrat.")
        return None

    # 1) Client
    while True:
        s = input("   🔗 ID du client : ").strip()
        if s.lower() == "retour":
            print("   ❌ Création annulée.")
            return None
        try:
            if not s.isdigit():
                raise ValueError("La valeur doit être un entier.")
            client_id = int(s)

            # existence en base
            with session_scope() as sess:
                if not ClientRepo(sess).get(client_id):
                    print("   ❌ Client introuvable.")
                    continue
            break
        except ValueError as e:
            print(f"   ❌ {e}")

    # 2) Montant total
    while True:
        s = input("   💼 Montant total (€) : ").strip()
        if s.lower() == "retour":
            print("   ❌ Création annulée.")
            return None
        try:
            total_amount = _parse_money(s)
            break
        except ValueError as e:
            print(f"   ❌ {e}")

    # 3) Montant dû
    while True:
        s = input("   💳 Montant dû (€)    : ").strip()
        if s.lower() == "retour":
            print("   ❌ Création annulée.")
            return None
        try:
            amount_due = _parse_money(s)
            if amount_due > total_amount:
                print("   ❌ Le montant dû ne peut pas dépasser le montant total.")
                continue
            break
        except ValueError as e:
            print(f"   ❌ {e}")

    # 4) Signé ?
    while True:
        s = input("   ✍️  Contrat signé ? (o/n) : ").strip()
        if s.lower() == "retour":
            print("   ❌ Création annulée.")
            return None
        try:
            is_signed = _parse_yes_no(s)
            break
        except ValueError as e:
            print(f"   ❌ {e}")

    # 5) (Optionnel) Commercial en charge (seulement si tu veux le saisir ici)
    #    Si non saisi, laisse None : tu pourras l’assigner plus tard.
    sales_contact_id: Optional[int] = None
    s = input("   🧑‍💼 ID du commercial (laisser vide pour aucun) : ").strip()
    if s.lower() == "retour":
        print("   ❌ Création annulée.")
        return None
    if s:
        if s.isdigit():
            sales_contact_id = int(s)
        else:
            print("   ⚠️ ID commercial ignoré (doit être un entier).")

    # Récap
    print("\n" + "-" * 50)
    print("📋  RÉCAPITULATIF DU CONTRAT".center(50))
    print("-" * 50)
    print(f"   🔗 Client ID     : {client_id}")
    print(f"   💼 Montant total : {total_amount:.2f} €")
    print(f"   💳 Montant dû    : {amount_due:.2f} €")
    print(f"   ✍️  Signé         : {'✅ Oui' if is_signed else '❌ Non'}")
    print(f"   🧑‍💼 Commercial    : {sales_contact_id if sales_contact_id else '—'}")
    print("-" * 50)

    confirm = input("   Confirmer la création ? (o/N) : ").strip().lower()
    if confirm != "o":
        print("   ❌ Création annulée.")
        return None

    # Construction de l'entité (laisse created_at/updated_at à None => DB default)
    contract = Contract(
        id=None,  # laissé à None, sera attribué par la DB
        client_id=client_id,
        sales_contact_id=sales_contact_id,
        total_amount=total_amount,
        amount_due=amount_due,
        is_signed=is_signed,
    )

    # Appel use-case (vérifie l'autorisation + persiste via repo)
    try:
        created = service.create(contract, auth=auth)
        print(f"✅ Contrat #{created.id} créé avec succès.")

        # 🔁 Met à jour le dernier contact du client = date de création du contrat
        lc_date = _as_utc_date(getattr(created, "created_at", None))
        with session_scope() as sess:
            repo = ClientRepo(sess)
            client = repo.get(client_id)
            if client:
                client.last_contact = lc_date  # type: ignore[assignment]
                repo.update(client)

        return created

    except AuthzError as e:
        print(f"⛔ Accès refusé : {e}")
    except Exception as e:
        print(f"❌ Erreur lors de la création : {e}")

    return None