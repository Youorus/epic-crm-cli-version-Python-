from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import (
    String, Integer, Boolean, ForeignKey, Text, LargeBinary,
    DateTime, Numeric
)

class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    date_joined: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    password_salt: Mapped[bytes | None] = mapped_column(LargeBinary)
    password_hash: Mapped[bytes | None] = mapped_column(LargeBinary)

class ClientModel(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_contact: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    sales_contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)

class ContractModel(Base):
    __tablename__ = "contracts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sales_contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    total_amount: Mapped[str] = mapped_column(Numeric(10, 2), nullable=False)
    amount_due: Mapped[str] = mapped_column(Numeric(10, 2), nullable=False)
    is_signed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)

class EventModel(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_id: Mapped[int] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    support_contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_start: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    event_end: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str] = mapped_column(String(500), nullable=False)
    attendees: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)