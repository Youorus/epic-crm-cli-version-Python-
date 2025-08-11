from models.clients import Client
from orm.models import ClientModel
from datetime import datetime, date


# Helper: safely convert ORM value to `date`
def _as_date(v):
    if v is None:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        # tolerate ISO strings ("YYYY-MM-DD" or full ISO datetime)
        try:
            return date.fromisoformat(v[:10])
        except Exception:
            raise ValueError("last_contact: format de date invalide")
    raise ValueError("last_contact: type invalide")


def client_to_entity(o: ClientModel) -> Client:
    return Client(
        id=o.id,
        full_name=o.full_name,
        email=o.email,
        phone=o.phone,
        company_name=o.company_name,
        last_contact=_as_date(o.last_contact),
        sales_contact_id=o.sales_contact_id,
        created_at=o.created_at,
        updated_at=o.updated_at,
    )

def client_new_orm(e: Client) -> ClientModel:
    return ClientModel(
        full_name=e.full_name,
        email=e.email,
        phone=e.phone,
        company_name=e.company_name,
        last_contact=e.last_contact,  # <-- date/datetime direct (ou None)
        sales_contact_id=e.sales_contact_id,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )

def client_apply(orm: ClientModel, e: Client) -> None:
    orm.full_name = e.full_name
    orm.email = e.email
    orm.phone = e.phone
    orm.company_name = e.company_name
    orm.last_contact = e.last_contact
    orm.sales_contact_id = e.sales_contact_id
    orm.updated_at = e.updated_at