# utils/sentry_init.py
from __future__ import annotations
import os
from pathlib import Path

import sentry_sdk
from dotenv import load_dotenv

# Charge .env à la racine du projet (ajuste si besoin)
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # …/PythonProject2
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)


def init_sentry() -> None:
    """
    Initialise Sentry selon les variables d'environnement.

    Variables utilisées :
    - SENTRY_ENABLE : "1" pour activer, sinon désactivé.
    - SENTRY_DSN : DSN fourni par Sentry.
    - SENTRY_ENV : Environnement (ex: dev, staging, prod).
    - SENTRY_RELEASE : Nom de release (ex: v1.0.0, local-dev).
    - SENTRY_TRACES : Taux de sampling des traces APM.
    - SENTRY_PROFILES : Taux de sampling du profiling.
    - SENTRY_DEBUG : "1" pour logs détaillés (utile en dev).
    """
    if os.getenv("SENTRY_ENABLE", "0") != "1":
        return

    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENV", "dev"),
        release=os.getenv("SENTRY_RELEASE", "local-dev"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES", "0.0")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES", "0.0")),
        send_default_pii=True,
        debug=os.getenv("SENTRY_DEBUG", "0") == "1",
    )
    print("✅ Sentry initialisé.")

# Permet de tester : python -m utils.sentry_init
if __name__ == "__main__":
    init_sentry()