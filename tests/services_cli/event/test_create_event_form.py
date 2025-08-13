import types
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

import pytest

from security.authorization import AuthContext, Role, AuthzError

MODULE = "cli.services.events.create_event_form"


def _dt(hours=0):
    return datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=hours)


@pytest.fixture
def form_mod(monkeypatch):
    """
    Raccourci: importe le module une fois et le renvoie.
    """
    import importlib
    mod = importlib.import_module(MODULE)
    return mod


def _fake_contract(cid=1, client_id=2):
    return SimpleNamespace(id=cid, client_id=client_id, is_signed=True)


def _make_services(event_create_return=None, event_create_side_effect=None):
    """
    Construit des services factices à passer au formulaire.
    - event_service.create renvoie `event_create_return` OU lève `event_create_side_effect`.
    - contract_service est factice (non utilisé si on monkeypatch _pick_signed_contract).
    """
    def _create(ev, auth=None):
        if event_create_side_effect:
            raise event_create_side_effect
        # si pas de retour fourni, renvoie l'event enrichi d'un id
        return event_create_return or SimpleNamespace(**vars(ev), id=42)

    event_service = SimpleNamespace(create=_create)
    contract_service = SimpleNamespace()
    return event_service, contract_service


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_create_event_cancel_when_pick_contract_returns_none(form_mod, monkeypatch):
    # _pick_signed_contract renvoie None -> annulation immédiate
    monkeypatch.setattr(form_mod, "_pick_signed_contract", lambda **kw: None)
    # On s'assure que create() ne sera jamais appelé
    event_service, contract_service = _make_services()
    auth = AuthContext(user_id=1, role=Role.GESTION)

    res = form_mod.create_event_form(
        event_service=event_service,
        contract_service=contract_service,
        auth=auth,
    )
    assert res is None




def test_create_event_invalid_dates_end_before_start(form_mod, monkeypatch):
    start = _dt(5)
    end = _dt(1)  # avant start -> invalide

    monkeypatch.setattr(form_mod, "_pick_signed_contract", lambda **kw: _fake_contract())
    monkeypatch.setattr(form_mod, "_req_str", lambda _p: "Bad order")
    # Ordre inversé
    calls = {"n": 0}
    def _req_dt_side(_p):
        calls["n"] += 1
        return start if calls["n"] == 1 else end
    monkeypatch.setattr(form_mod, "_req_dt", _req_dt_side)
    monkeypatch.setattr(form_mod, "_req_int_pos", lambda *_args, **_kw: 10)
    # Notes (sera ignoré car l'erreur survient avant)
    monkeypatch.setattr(form_mod, "input", lambda _p: "")

    event_service, contract_service = _make_services()
    auth = AuthContext(user_id=1, role=Role.GESTION)

    res = form_mod.create_event_form(
        event_service=event_service,
        contract_service=contract_service,
        auth=auth,
    )
    assert res is None  # pas de création


def test_create_event_cancel_on_confirm(form_mod, monkeypatch):
    start = _dt(1)
    end = _dt(2)

    monkeypatch.setattr(form_mod, "_pick_signed_contract", lambda **kw: _fake_contract())
    monkeypatch.setattr(form_mod, "_req_str", lambda _p: "Townhall")
    calls = {"n": 0}
    def _req_dt_side(_p):
        calls["n"] += 1
        return start if calls["n"] == 1 else end
    monkeypatch.setattr(form_mod, "_req_dt", _req_dt_side)
    monkeypatch.setattr(form_mod, "_req_int_pos", lambda *_args, **_kw: 100)
    # notes + (comme GESTION par défaut dans ce test), support id vide
    def _input_side(prompt):
        return ""  # notes vides et support vide -> pas d'assignation
    monkeypatch.setattr(form_mod, "input", _input_side)
    # Confirmation -> False
    monkeypatch.setattr(form_mod, "_confirm", lambda _p: False)

    event_service, contract_service = _make_services()
    auth = AuthContext(user_id=1, role=Role.GESTION)

    res = form_mod.create_event_form(
        event_service=event_service,
        contract_service=contract_service,
        auth=auth,
    )
    assert res is None



def test_create_event_authz_error_from_service(form_mod, monkeypatch):
    """
    Le use-case lève une AuthzError -> le formulaire retourne None proprement.
    """
    start = _dt(1)
    end = _dt(2)

    monkeypatch.setattr(form_mod, "_pick_signed_contract", lambda **kw: _fake_contract())
    monkeypatch.setattr(form_mod, "_req_str", lambda _p: "Board")
    calls = {"n": 0}
    def _req_dt_side(_p):
        calls["n"] += 1
        return start if calls["n"] == 1 else end
    monkeypatch.setattr(form_mod, "_req_dt", _req_dt_side)
    monkeypatch.setattr(form_mod, "_req_int_pos", lambda *_a, **_k: 5)
    # notes, support vide
    inputs = iter(["", ""])
    monkeypatch.setattr(form_mod, "input", lambda _p: next(inputs))
    monkeypatch.setattr(form_mod, "_confirm", lambda _p: True)

    # EventService.create lève AuthzError
    event_service, contract_service = _make_services(
        event_create_side_effect=AuthzError("nope")
    )
    auth = AuthContext(user_id=2, role=Role.GESTION)

    res = form_mod.create_event_form(
        event_service=event_service,
        contract_service=contract_service,
        auth=auth,
    )
    assert res is None