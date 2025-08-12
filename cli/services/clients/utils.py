from datetime import datetime, date
from typing import Any, Optional


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

# -------- Helpers de saisie/validation --------
def _req_str(prompt: str) -> Optional[str]:
    """
    Demande une chaîne non-vide. Retourne None si l'utilisateur tape 'retour'.
    Ne fait *aucun* print de debug pour éviter les doubles affichages.
    """
    while True:
        s = input(prompt).strip()
        if s.lower() == "retour":
            return None
        if s != "":
            return s
        print("   ❌ Champ obligatoire.")

def _opt_str(prompt: str) -> Optional[str]:
    """
    Demande une chaîne optionnelle (peut être vide). 'retour' annule.
    """
    s = input(prompt).strip()
    if s.lower() == "retour":
        return None
    return s or ""

def _confirm(prompt: str = "   Confirmer ? (o/N) : ") -> bool:
    return input(prompt).strip().lower() == "o"