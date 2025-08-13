from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone
from typing import List

import pytest

import cli.services.contracts.list_contracts as mod
from security.authorization import AuthContext, Role, AuthzError


# -------- Doubles de test --------

@dataclass
class FakeContract:
    id: int
    client_id: int
    sales_contact_id: int | None
    total_amount: object  # peut être Decimal/str/float, on teste la robustesse
    amount_due: object
    is_signed: bool
    created_at: datetime

    # labels optionnels que le renderer essaie de lire
    client_full_name: str | None = None
    sales_contact_username: str | None = None


class FakeServiceOK:
    def __init__(self, items: List[FakeContract]):
        self._items = items

    def list(self, *, auth: AuthContext):
        # le filtre métier/autorisation est supposé fait côté service
        return list(self._items)


class FakeServiceAuthzError:
    def list(self, *, auth: AuthContext):
        raise AuthzError("forbidden")


# -------- Fixtures utiles --------

@pytest.fixture
def auth_gestion() -> AuthContext:
    return AuthContext(user_id=1, role=Role.GESTION)


@pytest.fixture
def sample_contracts() -> list[FakeContract]:
    t0 = datetime(2025, 8, 11, 12, 0, tzinfo=timezone.utc)
    return [
        # total/dues en types variés pour tester _to_decimal
        FakeContract(
            id=1, client_id=10, sales_contact_id=2,
            total_amount=Decimal("5000.00"), amount_due="2000",
            is_signed=True, created_at=t0,
            client_full_name="Ada Lovelace", sales_contact_username="alice"
        ),
        FakeContract(
            id=2, client_id=11, sales_contact_id=None,
            total_amount="12000,00", amount_due="12000,00",  # virgule FR
            is_signed=False, created_at=t0,
            client_full_name="Grace Hopper", sales_contact_username=None
        ),
        FakeContract(
            id=3, client_id=12, sales_contact_id=3,
            total_amount=8000.0, amount_due=3000.0,
            is_signed=True, created_at=t0,
            client_full_name=None, sales_contact_username="bob"
        ),
    ]


# -------- Tests --------

def test_list_contracts_table_happy_path(capsys, auth_gestion, sample_contracts):
    svc = FakeServiceOK(sample_contracts)
    items = mod.list_contracts(service=svc, auth=auth_gestion, display=True, as_table=True)
    out = capsys.readouterr().out

    assert items and len(items) == 3
    assert "=== LISTE DES CONTRATS ===" in out
    # Vérifie quelques cellules formatées
    assert "Ada Lovelace" in out
    assert "Grace Hopper" in out
    assert "alice" in out or "alice".capitalize() in out  # commercial
    # Vérifie que l’icône signé apparait
    assert "✅" in out or "❌" in out


def test_list_contracts_detail_mode(capsys, auth_gestion, sample_contracts):
    svc = FakeServiceOK(sample_contracts)
    items = mod.list_contracts(service=svc, auth=auth_gestion, display=True, as_table=False)
    out = capsys.readouterr().out

    assert len(items) == 3
    assert "=== LISTE DES CONTRATS (détails) ===" in out
    # Présence de champs détaillés
    assert "Contrat       :" in out
    assert "Montant total" in out
    assert "Restant dû" in out


def test_filter_signed_true_only_signed(capsys, auth_gestion, sample_contracts):
    svc = FakeServiceOK(sample_contracts)
    items = mod.list_contracts(service=svc, auth=auth_gestion, display=False, filter_signed=True)
    # garde uniquement is_signed=True → ids 1 et 3
    ids = [c.id for c in items]
    assert ids == [1, 3]


def test_filter_signed_false_only_unsigned(capsys, auth_gestion, sample_contracts):
    svc = FakeServiceOK(sample_contracts)
    items = mod.list_contracts(service=svc, auth=auth_gestion, display=False, filter_signed=False)
    # garde uniquement is_signed=False → id 2
    ids = [c.id for c in items]
    assert ids == [2]


def test_min_due_filters_out_zero_or_small_due(capsys, auth_gestion, sample_contracts):
    # amount_due: 2000, 12000, 3000
    svc = FakeServiceOK(sample_contracts)
    items = mod.list_contracts(service=svc, auth=auth_gestion, display=False, min_due=2500)
    ids = [c.id for c in items]
    # >= 2500 → ids 2 et 3 (12000, 3000)
    assert ids == [2, 3]


def test_display_false_returns_items_without_print(capsys, auth_gestion, sample_contracts):
    svc = FakeServiceOK(sample_contracts)
    items = mod.list_contracts(service=svc, auth=auth_gestion, display=False)
    out = capsys.readouterr().out
    assert len(items) == 3
    # Aucun header imprimé
    assert "LISTE DES CONTRATS" not in out


def test_no_items_prints_nothing_else_than_notice(capsys, auth_gestion):
    svc = FakeServiceOK(items=[])
    items = mod.list_contracts(service=svc, auth=auth_gestion, display=True)
    out = capsys.readouterr().out
    assert items == []
    assert "Aucun contrat trouvé" in out


def test_authz_error_is_caught_and_printed(capsys, auth_gestion):
    svc = FakeServiceAuthzError()
    items = mod.list_contracts(service=svc, auth=auth_gestion, display=True)
    out = capsys.readouterr().out
    assert items == []
    assert "Accès refusé" in out