from datetime import datetime, timezone, date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional, Any

from services.crud.client_repo import ClientRepo
from services.db_session import session_scope


# ─────────────────────────────────────────────────────────
# Helpers parsing / validation
# ─────────────────────────────────────────────────────────
def _parse_money(raw: str) -> Decimal:
    """
    Accepte : '1 234,50', '1234.50', '1 234,50 €', '1234', etc.
    Retourne un Decimal(2 décimales) ou lève ValueError.
    """
    if raw is None:
        raise ValueError("Montant requis.")
    s = str(raw).strip()
    if not s:
        raise ValueError("Montant requis.")

    # Nettoyage : enlève symbole euro + tous les espaces (classiques & insécables)
    for ch in ("€", " ", "\u00A0", "\u202F"):
        s = s.replace(ch, "")
    s = s.replace(",", ".")  # virgule -> point

    try:
        d = Decimal(s)
    except (InvalidOperation, ValueError):
        raise ValueError("Montant invalide.")

    if d < 0:
        raise ValueError("Le montant ne peut pas être négatif.")

    # 2 décimales
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _parse_yes_no(raw: str) -> bool:
    s = (raw or "").strip().lower()
    if s in ("o", "oui", "y", "yes", "1", "true", "vrai"):
        return True
    if s in ("n", "non", "no", "0", "false", "faux"):
        return False
    raise ValueError("Répondez par oui/oui (o) ou non (n).")


def _input_int(prompt: str, allow_blank: bool = False) -> Optional[int]:
    s = input(prompt).strip()
    if allow_blank and s == "":
        return None
    if not s.isdigit():
        raise ValueError("La valeur doit être un entier.")
    return int(s)


def _as_utc_date(dt: Optional[datetime]) -> date:
    """
    Convertit un datetime (aware/naive/None) en date (YYYY-MM-DD).
    Si None, utilise maintenant (UTC).
    """
    if dt is None:
        return datetime.now(timezone.utc).date()
    if dt.tzinfo is None:
        # Considère naive comme UTC (évite les surprises)
        return dt.replace(tzinfo=timezone.utc).date()
    return dt.astimezone(timezone.utc).date()


# ─────────────────────────────────────────────────────────
# Sélection/validation client
# ─────────────────────────────────────────────────────────
def _pick_client_id() -> int:
    """
    Demande un client_id et vérifie son existence en base.
    Retourne le client_id si OK, lève ValueError sinon.
    """
    with session_scope() as sess:
        repo = ClientRepo(sess)

        while True:
            try:
                cid = _input_int("   🔗 ID du client : ")
            except ValueError as e:
                print(f"   ❌ {e}")
                continue

            client = repo.get(cid) if cid is not None else None
            if not client:
                print("   ❌ Client introuvable. Réessayez.")
                continue

            print(f"   ✅ Client: {client.full_name} — {client.company_name}")
            return cid  # type: ignore[return-value]



# ─────────────────────────────────────────────────────────────────────────────
# Helpers de normalisation / affichage
# ─────────────────────────────────────────────────────────────────────────────

def _clip(val: Any, width: int) -> str:
    """Coupe proprement une chaîne pour tenir dans 'width' colonnes."""
    s = "" if val is None else str(val)
    return (s[: width - 1] + "…") if len(s) > width else s


def _to_decimal(val: Any) -> Decimal:
    """
    Convertit n’importe quelle valeur en Decimal(2 décimales) de façon robuste.
    Accepte Decimal, int, float, str (avec €, espaces, séparateur ','), None.
    """
    if val is None:
        return Decimal("0.00")

    if isinstance(val, Decimal):
        # force 2 décimales
        return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if isinstance(val, (int, float)):
        # float -> passer par str pour éviter les surprises binaires
        return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # str (ou autre -> cast en str)
    s = str(val).strip()
    if not s:
        return Decimal("0.00")

    # nettoyer symbole € + espaces (y compris espace fine insécable)
    s = s.replace("€", "").replace("\u202f", "").replace(" ", "")
    # séparateur FR -> EN
    s = s.replace(",", ".")

    try:
        return Decimal(s).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        # Valeur irrécupérable -> 0.00
        return Decimal("0.00")


def _to_float(val: Any) -> float:
    """Retourne un float à partir de n’importe quelle valeur monétaire."""
    return float(_to_decimal(val))


def _fmt_euro(amount: Any) -> str:
    """
    Formate proprement en euros (12 345,67 €), quelle que soit la forme d’entrée.
    On passe toujours par Decimal → float pour un formatage stable.
    """
    v = _to_float(amount)
    txt = f"{v:,.2f}".replace(",", " ").replace(".", ",")  # 12345.67 -> "12 345,67"
    return f"{txt} €"


def _date_only(val: Any) -> str:
    """Affiche YYYY-MM-DD si val est un datetime/date, sinon retourne tel quel."""
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d")
    return str(val) if val is not None else "—"


# ─────────────────────────────────────────────────────────
# Helpers parsing / validation (alignés avec create_contract_form)
# ─────────────────────────────────────────────────────────
def _parse_money(raw: str) -> Decimal:
    """
    Accepte : '1 234,50', '1234.50', '1 234,50 €', '1234', etc.
    Retourne un Decimal(2 décimales) ou lève ValueError.
    """
    if raw is None:
        raise ValueError("Montant requis.")
    s = str(raw).strip()
    if not s:
        raise ValueError("Montant requis.")
    for ch in ("€", " ", "\u00A0", "\u202F"):
        s = s.replace(ch, "")
    s = s.replace(",", ".")
    try:
        d = Decimal(s)
    except (InvalidOperation, ValueError):
        raise ValueError("Montant invalide.")
    if d < 0:
        raise ValueError("Le montant ne peut pas être négatif.")
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _parse_yes_no_optional(raw: str, *, default: bool) -> bool:
    s = (raw or "").strip().lower()
    if s == "":
        return default
    if s in ("o", "oui", "y", "yes", "1", "true", "vrai"):
        return True
    if s in ("n", "non", "no", "0", "false", "faux"):
        return False
    raise ValueError("Répondez par oui/oui (o) ou non (n), ou laissez vide pour conserver la valeur.")


def _input_int_optional(prompt: str) -> Optional[int]:
    """
    Lit un entier ou vide (→ None).
    """
    s = input(prompt).strip()
    if s == "":
        return None
    if not s.isdigit():
        raise ValueError("La valeur doit être un entier.")
    return int(s)


def _input_money_optional(prompt: str) -> Optional[Decimal]:
    s = input(prompt).strip()
    if s == "":
        return None
    return _parse_money(s)

