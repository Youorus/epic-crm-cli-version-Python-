from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    """
    Rôles fonctionnels des utilisateurs dans l'application.

    Hérite de `str` et `Enum` pour :
    - compatibilité avec JSON, Pydantic, bases de données
    - facilité de comparaison (ex: `role == "COMMERCIAL"`)

    Valeurs :
        COMMERCIAL : rôle commercial (gestion prospects/clients)
        SUPPORT    : rôle support (gestion événements/contrats)
        GESTION    : rôle gestion (administration globale)
    """

    COMMERCIAL = "COMMERCIAL"
    SUPPORT = "SUPPORT"
    GESTION = "GESTION"
