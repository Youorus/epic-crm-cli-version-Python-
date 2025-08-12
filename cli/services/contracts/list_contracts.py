# cli/services/contracts/list_contracts.py
from __future__ import annotations

from typing import List, Optional, Any
from datetime import datetime, date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from cli.services.contracts.utils import _to_decimal, _clip, _fmt_euro, _date_only
from services.usecases.contract_crud import ContractService
from security.authorization import AuthContext, AuthzError


# ─────────────────────────────────────────────────────────────────────────────
# Service CLI : liste des contrats
# ─────────────────────────────────────────────────────────────────────────────

def list_contracts(
    *,
    service: ContractService,
    auth: AuthContext,
    display: bool = True,
    as_table: bool = True,
    filter_signed: Optional[bool] = None,
    min_due: Optional[float] = None,
) -> List:
    """
    Liste les contrats via le use-case Python (pas d'API REST).

    Paramètres
    ----------
    service : ContractService
        Use-case métier (accès repo + règles d'autorisation).
    auth : AuthContext
        Contexte d'authentification/autorisation courant.
    display : bool
        Si True, affiche la liste dans la console.
    as_table : bool
        Si True, format "tableau" ; sinon, affichage détaillé.
    filter_signed : Optional[bool]
        Si précisé, filtre les contrats signés True/False.
    min_due : Optional[float]
        Si précisé, ne garde que les contrats dont le montant dû >= min_due.

    Retour
    ------
    List[Contract] : la liste (éventuellement filtrée).
    """
    try:
        items = service.list(auth=auth)  # Autorisation + filtrage métier
    except AuthzError as e:
        print(f"❌ Accès refusé : {e}")
        return []
    except Exception as e:
        print(f"❌ Erreur inattendue lors du listing des contrats : {e}")
        return []

    # Filtres optionnels côté CLI
    if filter_signed is not None:
        items = [c for c in items if bool(getattr(c, "is_signed", False)) is filter_signed]

    if min_due is not None:
        threshold = _to_decimal(min_due)  # normalise la borne aussi
        items = [c for c in items if _to_decimal(getattr(c, "amount_due", 0)) >= threshold]

    if not items:
        if display:
            print("🔍 Aucun contrat trouvé.")
        return items

    if not display:
        return items

    # ─────────────────────────────────────────────────────────
    # Affichage tableau (compact)
    # ─────────────────────────────────────────────────────────
    if as_table:
        W_ID, W_CLIENT, W_SALES, W_TOTAL, W_PAID, W_DUE, W_SIGNED, W_DATE = 5, 22, 16, 12, 12, 12, 7, 10

        header = (
            f"{'ID':<{W_ID}} "
            f"{'Client':<{W_CLIENT}} "
            f"{'Commercial':<{W_SALES}} "
            f"{'Total':>{W_TOTAL}} "
            f"{'Payé':>{W_PAID}} "
            f"{'Restant':>{W_DUE}} "
            f"{'Signé':<{W_SIGNED}} "
            f"{'Créé le':<{W_DATE}}"
        )

        print("\n📄 === LISTE DES CONTRATS ===")
        print(header)
        print("-" * len(header))

        for c in items:
            try:
                total = _to_decimal(getattr(c, "total_amount", 0))
                due = _to_decimal(getattr(c, "amount_due", 0))
                paid = (total - due)
                if paid < Decimal("0.00"):
                    paid = Decimal("0.00")

                client_label = (
                    getattr(c, "client_full_name", None)
                    or getattr(getattr(c, "client", None), "full_name", None)
                    or f"Client #{getattr(c, 'client_id', 'N/A')}"
                )
                sales_label = (
                    getattr(c, "sales_contact_username", None)
                    or getattr(getattr(c, "sales_contact", None), "username", None)
                    or (f"User #{getattr(c, 'sales_contact_id', 'N/A')}" if getattr(c, "sales_contact_id", None) else "—")
                )

                created = getattr(c, "created_at", getattr(c, "date_created", None))

                row = (
                    f"{str(getattr(c, 'id', '')):<{W_ID}} "
                    f"{_clip(client_label, W_CLIENT):<{W_CLIENT}} "
                    f"{_clip(sales_label, W_SALES):<{W_SALES}} "
                    f"{_fmt_euro(total):>{W_TOTAL}} "
                    f"{_fmt_euro(paid):>{W_PAID}} "
                    f"{_fmt_euro(due):>{W_DUE}} "
                    f"{('✅' if getattr(c, 'is_signed', False) else '❌'):<{W_SIGNED}} "
                    f"{_date_only(created):<{W_DATE}}"
                )
                print(row)
            except Exception as e:
                # On continue l’affichage même si un contrat est “sale”
                cid = getattr(c, "id", "?")
                print(f"⚠️  Contrat #{cid} ignoré (donnée invalide) : {e}")

        return items

    # ─────────────────────────────────────────────────────────
    # Affichage détaillé
    # ─────────────────────────────────────────────────────────
    print("\n📄 === LISTE DES CONTRATS (détails) ===")
    for c in items:
        try:
            total = _to_decimal(getattr(c, "total_amount", 0))
            due = _to_decimal(getattr(c, "amount_due", 0))
            paid = (total - due)
            if paid < Decimal("0.00"):
                paid = Decimal("0.00")

            client_label = (
                getattr(c, "client_full_name", None)
                or getattr(getattr(c, "client", None), "full_name", None)
                or f"Client #{getattr(c, 'client_id', 'N/A')}"
            )
            sales_label = (
                getattr(c, "sales_contact_username", None)
                or getattr(getattr(c, "sales_contact", None), "username", None)
                or (f"User #{getattr(c, 'sales_contact_id', 'N/A')}" if getattr(c, "sales_contact_id", None) else "—")
            )
            created = getattr(c, "created_at", getattr(c, "date_created", None))

            print("\n" + "-" * 50)
            print(f"🆔 Contrat       : {getattr(c, 'id', '—')}")
            print(f"👤 Client        : {client_label}")
            print(f"🧑‍💼 Commercial   : {sales_label}")
            print(f"💼 Montant total : {_fmt_euro(total)}")
            print(f"💳 Payé          : {_fmt_euro(paid)}")
            print(f"📉 Restant dû    : {_fmt_euro(due)}")
            print(f"✍️  Signé         : {'✅ Oui' if getattr(c, 'is_signed', False) else '❌ Non'}")
            print(f"📅 Créé le       : {_date_only(created)}")
        except Exception as e:
            cid = getattr(c, "id", "?")
            print(f"⚠️  Contrat #{cid} ignoré (donnée invalide) : {e}")

    return items