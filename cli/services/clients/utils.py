from datetime import datetime, date
from typing import Any


def _clip(val: Any, width: int) -> str:
    """Coupe proprement une chaîne pour tenir dans 'width' colonnes (ajoute '…' si tronquée)."""
    s = "" if val is None else str(val)
    return (s[: width - 1] + "…") if len(s) > width else s


def _fmt_dt(value: Any) -> str:
    """Formate date/datetime/str → 'YYYY-MM-DD HH:MM' (ou 'YYYY-MM-DD' pour les dates)."""
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    # fallback string/int
    return str(value)