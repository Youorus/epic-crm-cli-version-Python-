# src/your_app/adapters/persistence/sqlalchemy/models.py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[str | None]
    date_joined: Mapped[str]
    created_at: Mapped[str]
    updated_at: Mapped[str]
    password_salt: Mapped[bytes | None]
    password_hash: Mapped[bytes | None]

class ClientModel(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_contact: Mapped[str | None]
    sales_contact_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[str]
    updated_at: Mapped[str]

class ContractModel(Base):
    __tablename__ = "contracts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    sales_contact_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    total_amount: Mapped[str] = mapped_column(String(32), nullable=False)
    amount_due: Mapped[str] = mapped_column(String(32), nullable=False)
    is_signed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[str]
    updated_at: Mapped[str]

class EventModel(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), unique=True, nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    support_contact_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_start: Mapped[str] = mapped_column(String(64), nullable=False)
    event_end: Mapped[str] = mapped_column(String(64), nullable=False)
    location: Mapped[str] = mapped_column(String(500), nullable=False)
    attendees: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[str]
    updated_at: Mapped[str]