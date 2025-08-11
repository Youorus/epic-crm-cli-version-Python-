from models.clients import Client
from orm.models import ClientModel
from datetime import datetime, date


def client_to_entity(o: ClientModel) -> Client:
    return Client(
        id=o.id,
        full_name=o.full_name,
        email=o.email,
        phone=o.phone,
        company_name=o.company_name,
        last_contact=date.fromisoformat(o.last_contact) if o.last_contact else None,
        sales_contact_id=o.sales_contact_id,
        created_at=datetime.fromisoformat(o.created_at),
        updated_at=datetime.fromisoformat(o.updated_at),
    )

def client_new_orm(e: Client) -> ClientModel:
    return ClientModel(
        full_name=e.full_name,
        email=e.email,
        phone=e.phone,
        company_name=e.company_name,
        last_contact=e.last_contact.isoformat() if e.last_contact else None,
        sales_contact_id=e.sales_contact_id,
        created_at=e.created_at.isoformat(),
        updated_at=e.updated_at.isoformat(),
    )

def client_apply(orm: ClientModel, e: Client) -> None:
    orm.full_name = e.full_name
    orm.email = e.email
    orm.phone = e.phone
    orm.company_name = e.company_name
    orm.last_contact = e.last_contact.isoformat() if e.last_contact else None
    orm.sales_contact_id = e.sales_contact_id
    orm.updated_at = e.updated_at.isoformat()