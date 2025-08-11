# orm/models.py
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import (
    String, Integer, Boolean, ForeignKey, Text, LargeBinary,
    DateTime, Date, Numeric, CheckConstraint, func, Index
)


class Base(DeclarativeBase):
    pass


# =========================
# USERS
# =========================
class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_joined: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    password_salt: Mapped[bytes | None] = mapped_column(LargeBinary)
    password_hash: Mapped[bytes | None] = mapped_column(LargeBinary)

    __table_args__ = (
        Index("ix_users_username", "username"),
    )


# =========================
# CLIENTS
# =========================
class ClientModel(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # -> Date (pas DateTime) comme dans ton modèle d'origine
    last_contact: Mapped[datetime | None] = mapped_column(Date())

    sales_contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_clients_sales_contact_id", "sales_contact_id"),
        Index("ix_clients_company_name", "company_name"),
    )


# =========================
# CONTRACTS
# =========================
class ContractModel(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    sales_contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    # IMPORTANT: Decimal + asdecimal=True
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2, asdecimal=True), nullable=False)
    amount_due:   Mapped[Decimal] = mapped_column(Numeric(10, 2, asdecimal=True), nullable=False)

    is_signed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_contracts_total_amount_nonneg"),
        CheckConstraint("amount_due >= 0",   name="ck_contracts_amount_due_nonneg"),
        Index("ix_contracts_sales_contact_id", "sales_contact_id"),
    )


# =========================
# EVENTS
# =========================
class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    contract_id: Mapped[int] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    support_contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_end:   Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str] = mapped_column(String(500), nullable=False)
    attendees: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, server_default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("attendees >= 1", name="ck_events_attendees_pos"),
    )