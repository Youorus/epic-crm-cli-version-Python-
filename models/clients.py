from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional, Dict, Any
from validators.client_validators import (
    validate_client_full_name,
    validate_client_email,
    validate_client_phone,
    validate_company_name,
    validate_last_contact,
)

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(slots=True)
class Client:
    # Identité & coordonnées
    full_name: str
    email: str
    phone: str
    company_name: str

    # Suivi commercial
    last_contact: Optional[date] = None
    sales_contact_id: Optional[int] = None  # int au lieu de UUID

    # Techniques
    id: Optional[int] = None
    created_at: datetime = field(default_factory=_utcnow, kw_only=True)
    updated_at: datetime = field(default_factory=_utcnow, kw_only=True)

    def __post_init__(self) -> None:
        self.full_name = validate_client_full_name(self.full_name)
        self.email = validate_client_email(self.email)
        self.phone = validate_client_phone(self.phone)
        self.company_name = validate_company_name(self.company_name)
        if self.last_contact is not None:
            self.last_contact = validate_last_contact(self.last_contact)

    # Métier
    def touch(self) -> None:
        self.updated_at = _utcnow()

    def assign_sales_contact(self, user_id: Optional[int]) -> None:
        self.sales_contact_id = user_id
        self.touch()

    def record_contact(self, when: Optional[date] = None) -> None:
        self.last_contact = when or date.today()
        self.touch()

    def update_contact_info(
        self,
        *,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> None:
        if full_name is not None:
            self.full_name = validate_client_full_name(full_name)
        if email is not None:
            self.email = validate_client_email(email)
        if phone is not None:
            self.phone = validate_client_phone(phone)
        if company_name is not None:
            self.company_name = validate_company_name(company_name)
        self.touch()

    # Sérialisation
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "company_name": self.company_name,
            "last_contact": self.last_contact.isoformat() if self.last_contact else None,
            "sales_contact_id": self.sales_contact_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def create(
        cls,
        *,
        full_name: str,
        email: str,
        phone: str,
        company_name: str,
        last_contact: Optional[date] = None,
        sales_contact_id: Optional[int] = None,
    ) -> "Client":
        return cls(
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company_name,
            last_contact=last_contact,
            sales_contact_id=sales_contact_id,
        )

    def __str__(self) -> str:
        return f"{self.full_name} - {self.company_name}"