# utils/seed.py
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from contextlib import contextmanager

# --- Assurer l'import local en priorité ---
ROOT = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# --- ORM / Session ---
from orm.db import SessionLocal

# --- Repositories (adapters ORM) ---
from services.crud.user_repo import UserRepo
from services.crud.client_repo import ClientRepo
from services.crud.contract_repo import ContractRepo
from services.crud.event_repo import EventRepo

# --- ORM models (pour accès direct si besoin) ---
from orm.models import UserModel, ClientModel, ContractModel, EventModel

# --- Entités domaine ---
from models.users import User
from models.clients import Client
from models.contract import Contract
from models.event import Event

# --- Enum rôles ---
from enums.user_role import UserRole

# ----------------------------
# Contexte & helpers généraux
# ----------------------------
UTC = timezone.utc
NOW = datetime.now(UTC)


def _dt(hours_from_now: int) -> datetime:
    return NOW + timedelta(hours=hours_from_now)


@contextmanager
def session_scope():
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def _dec(v) -> Decimal:
    """Normalise en Decimal(2 décimales) sans jamais renvoyer de str."""
    if v is None:
        return Decimal("0.00")
    if isinstance(v, Decimal):
        return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if isinstance(v, (int, float)):
        return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    # str ou autres
    s = str(v).strip()
    s = s.replace("€", "").replace("\u202f", "").replace(" ", "").replace(",", ".")
    if not s:
        return Decimal("0.00")
    try:
        return Decimal(s).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


# ----------------------------
# Helpers idempotents
# ----------------------------
def get_or_create_user(repo: UserRepo, *, email: str, username: str, role: UserRole, password: str) -> User:
    existing = repo.s.query(UserModel).filter(UserModel.email == email).one_or_none()
    if existing:
        # Map minimal → Entité User (on garde les datetimes de l’ORM tels quels)
        u = User(
            id=existing.id,
            username=existing.username,
            email=existing.email,
            role=UserRole(existing.role),
            is_active=getattr(existing, "is_active", True),
            is_staff=getattr(existing, "is_staff", False),
            is_superuser=getattr(existing, "is_superuser", False),
            date_joined=existing.date_joined,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
            last_login=existing.last_login,
        )
        return u

    u = User.create(username=username, email=email, role=role, password=password)
    return repo.add(u)


def get_or_create_client(
        repo: ClientRepo,
        *,
        email: str,
        full_name: str,
        phone: str,
        company_name: str,
        sales_contact_id: int | None,
) -> Client:
    existing = repo.s.query(ClientModel).filter(ClientModel.email == email).one_or_none()
    if existing:
        return Client(
            id=existing.id,
            full_name=existing.full_name,
            email=existing.email,
            phone=existing.phone,
            company_name=existing.company_name,
            last_contact=existing.last_contact,  # date ou None
            sales_contact_id=existing.sales_contact_id,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
    c = Client.create(
        full_name=full_name,
        email=email,
        phone=phone,
        company_name=company_name,
        sales_contact_id=sales_contact_id,
    )
    return repo.add(c)


def get_or_create_contract(
        repo: ContractRepo,
        *,
        client_id: int,
        sales_contact_id: int | None,
        total_amount: Decimal,
        amount_due: Decimal,
        is_signed: bool,
) -> Contract:
    # Comparaison NUMÉRIQUE (surtout pas str(total_amount))
    existing = (
        repo.s.query(ContractModel)
        .filter(
            ContractModel.client_id == client_id,
            ContractModel.total_amount == _dec(total_amount),
            ContractModel.amount_due == _dec(amount_due),
            ContractModel.is_signed == is_signed,
        )
        .one_or_none()
    )
    if existing:
        return Contract(
            id=existing.id,
            client_id=existing.client_id,
            sales_contact_id=existing.sales_contact_id,
            total_amount=_dec(existing.total_amount),
            amount_due=_dec(existing.amount_due),
            is_signed=bool(existing.is_signed),
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )

    c = Contract.create(
        client_id=client_id,
        sales_contact_id=sales_contact_id,
        total_amount=_dec(total_amount),
        amount_due=_dec(amount_due),
        is_signed=is_signed,
    )
    created = repo.add(c)

    # 👉 Met à jour last_contact du client à la date du contrat créé
    #    (si tu préfères “dernier contrat signé uniquement”, ajoute une condition sur is_signed)
    cm = repo.s.get(ClientModel, client_id)
    if cm:
        cm.last_contact = (created.created_at or NOW).date()
        repo.s.add(cm)

    return created


def get_or_create_event(
        repo: EventRepo,
        *,
        contract_id: int,
        client_id: int,
        event_name: str,
        start: datetime,
        end: datetime,
        location: str,
        attendees: int,
        support_contact_id: int | None,
        notes: str = "",
) -> Event:
    # Unicité : OneToOne sur contract_id
    existing = repo.s.query(EventModel).filter(EventModel.contract_id == contract_id).one_or_none()
    if existing:
        return Event(
            id=existing.id,
            contract_id=existing.contract_id,
            client_id=existing.client_id,
            support_contact_id=existing.support_contact_id,
            event_name=existing.event_name,
            event_start=existing.event_start,
            event_end=existing.event_end,
            location=existing.location,
            attendees=existing.attendees,
            notes=existing.notes or "",
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
    e = Event.create(
        contract_id=contract_id,
        client_id=client_id,
        support_contact_id=support_contact_id,
        event_name=event_name,
        event_start=start,
        event_end=end,
        location=location,
        attendees=attendees,
        notes=notes,
    )
    return repo.add(e)


# ----------------------------
# Seed principal
# ----------------------------
def run_seed(password_plain: str = "Azerty123$") -> None:
    with session_scope() as s:
        user_repo = UserRepo(s)
        client_repo = ClientRepo(s)
        contract_repo = ContractRepo(s)
        event_repo = EventRepo(s)

        # Users (3)
        gestion = get_or_create_user(
            user_repo, email="gestion@epic-events.com", username="gestion",
            role=UserRole.GESTION, password=password_plain
        )
        commercial = get_or_create_user(
            user_repo, email="commercial@epic-events.com", username="commercial",
            role=UserRole.COMMERCIAL, password=password_plain
        )
        support = get_or_create_user(
            user_repo, email="support@epic-events.com", username="support",
            role=UserRole.SUPPORT, password=password_plain
        )
        print(f"Users OK: gestion={gestion.id}, commercial={commercial.id}, support={support.id}")

        # Clients (3) → assignés au commercial
        ada = get_or_create_client(
            client_repo,
            email="ada@example.com",
            full_name="Ada Lovelace",
            phone="+33 1 23 45 67 89",
            company_name="Analytical Engines",
            sales_contact_id=commercial.id,
        )
        grace = get_or_create_client(
            client_repo,
            email="grace@example.com",
            full_name="Grace Hopper",
            phone="+33 6 12 34 56 78",
            company_name="COBOL Inc.",
            sales_contact_id=commercial.id,
        )
        alan = get_or_create_client(
            client_repo,
            email="alan@example.com",
            full_name="Alan Turing",
            phone="+44 20 7946 0958",
            company_name="Enigma Ltd",
            sales_contact_id=commercial.id,
        )
        print(f"Clients OK: {ada.id}, {grace.id}, {alan.id}")

        # Contrats (2 signés, 1 non signé) — montants en Decimal
        c1 = get_or_create_contract(
            contract_repo,
            client_id=ada.id,  # type: ignore[arg-type]
            sales_contact_id=commercial.id,
            total_amount=Decimal("5000.00"),
            amount_due=Decimal("2000.00"),
            is_signed=True,
        )
        c2 = get_or_create_contract(
            contract_repo,
            client_id=grace.id,  # type: ignore[arg-type]
            sales_contact_id=commercial.id,
            total_amount=Decimal("12000.00"),
            amount_due=Decimal("12000.00"),
            is_signed=False,
        )
        c3 = get_or_create_contract(
            contract_repo,
            client_id=alan.id,  # type: ignore[arg-type]
            sales_contact_id=commercial.id,
            total_amount=Decimal("8000.00"),
            amount_due=Decimal("3000.00"),
            is_signed=True,
        )
        print(f"Contracts OK: {c1.id}(signé), {c2.id}(non signé), {c3.id}(signé)")

        # Événements (sur contrats signés)
        e1 = get_or_create_event(
            event_repo,
            contract_id=c1.id,  # type: ignore[arg-type]
            client_id=ada.id,  # type: ignore[arg-type]
            event_name="Ada Wedding",
            start=_dt(24),
            end=_dt(36),
            location="53 Rue du Château, 41120 Candé-sur-Beuvron, France",
            attendees=75,
            support_contact_id=support.id,
            notes="Wedding at 3PM by the river. Catering OK, reception at 5PM. Need DJ.",
        )
        e2 = get_or_create_event(
            event_repo,
            contract_id=c3.id,  # type: ignore[arg-type]
            client_id=alan.id,  # type: ignore[arg-type]
            event_name="General Assembly",
            start=_dt(72),
            end=_dt(74),
            location="Salle des fêtes de Mufflins",
            attendees=200,
            support_contact_id=None,
            notes="Assemblée générale des actionnaires (~200 personnes).",
        )
        print(f"Events OK: {e1.id} (contract {e1.contract_id}), {e2.id} (contract {e2.contract_id})")

    print("🎯 Seed terminé.")


if __name__ == "__main__":
    run_seed()
