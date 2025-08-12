# services/crud/contract_repo.py (ou ton fichier équivalent)

from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Numeric, Boolean, Integer, DateTime, ForeignKey, func, CheckConstraint, Index
from datetime import datetime

from models.contract import Contract  # ton dataclass/entité côté domaine
from orm.models import Base, ContractModel


# ---------- Helpers de normalisation ----------
def _norm_decimal(v: Any) -> Decimal:
    """
    Convertit proprement n'importe quelle valeur (Decimal/float/int/str)
    en Decimal(10,2) (arrondi à 2 décimales).
    - Gère les chaînes '1 234,56 €' -> Decimal('1234.56')
    - Tolère None -> Decimal('0.00')
    """
    if v is None:
        return Decimal("0.00")

    if isinstance(v, Decimal):
        q = v.quantize(Decimal("0.01"))
        return q

    if isinstance(v, (int, float)):
        return Decimal(str(v)).quantize(Decimal("0.01"))

    s = str(v).strip()
    # Nettoyage courant : euro, espaces (y compris insécables), virgules
    s = s.replace("€", "").replace("\u202f", "").replace(" ", "")
    s = s.replace(",", ".")
    if s == "":
        return Decimal("0.00")
    try:
        return Decimal(s).quantize(Decimal("0.01"))
    except InvalidOperation:
        # Dernier filet de sécurité
        return Decimal("0.00")

# ---------- Mapping ORM -> Entité ----------
def contract_to_entity(orm: ContractModel) -> Contract:
    return Contract(
        id=orm.id,
        client_id=orm.client_id,
        sales_contact_id=orm.sales_contact_id,
        total_amount=_norm_decimal(orm.total_amount),
        amount_due=_norm_decimal(orm.amount_due),
        is_signed=bool(orm.is_signed),
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


# ---------- Mapping Entité -> ORM (nouvel objet) ----------
def contract_new_orm(e: Contract) -> ContractModel:
    return ContractModel(
        client_id=e.client_id,
        sales_contact_id=e.sales_contact_id,
        total_amount=_norm_decimal(e.total_amount),
        amount_due=_norm_decimal(e.amount_due),
        is_signed=bool(e.is_signed),
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


# ---------- Mapping Entité -> ORM (apply sur existant) ----------
def contract_apply(orm: ContractModel, e: Contract) -> ContractModel:
    orm.client_id = e.client_id
    orm.sales_contact_id = e.sales_contact_id
    orm.total_amount = _norm_decimal(e.total_amount)
    orm.amount_due = _norm_decimal(e.amount_due)
    orm.is_signed = bool(e.is_signed)
    orm.updated_at = e.updated_at or orm.updated_at
    return orm