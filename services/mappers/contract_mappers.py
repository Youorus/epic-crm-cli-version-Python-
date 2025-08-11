from decimal import Decimal
from datetime import datetime

from models.contract import Contract
from orm.models import ContractModel


def _to_dec(s: str) -> Decimal:
    # Numeric -> str via SA ; on retransforme proprement
    return Decimal(str(s))

def contract_to_entity(o: ContractModel) -> Contract:
    return Contract(
        id=o.id,
        client_id=o.client_id,
        sales_contact_id=o.sales_contact_id,
        total_amount=_to_dec(o.total_amount),
        amount_due=_to_dec(o.amount_due),
        is_signed=o.is_signed,
        created_at=datetime.fromisoformat(o.created_at),
        updated_at=datetime.fromisoformat(o.updated_at),
    )

def contract_new_orm(e: Contract) -> ContractModel:
    return ContractModel(
        client_id=e.client_id,
        sales_contact_id=e.sales_contact_id,
        total_amount=e.total_amount,  # <-- Decimal direct (colonne Numeric)
        amount_due=e.amount_due,  # <-- Decimal direct
        is_signed=e.is_signed,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )

def contract_apply(orm: ContractModel, e: Contract) -> None:
    orm.client_id = e.client_id
    orm.sales_contact_id = e.sales_contact_id
    orm.total_amount = e.total_amount  # <-- pas str()
    orm.amount_due = e.amount_due
    orm.is_signed = e.is_signed
    orm.updated_at = e.updated_at