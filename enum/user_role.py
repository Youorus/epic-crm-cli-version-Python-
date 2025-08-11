from enum import Enum


class UserRole(str, Enum):
    COMMERCIAL = "COMMERCIAL"
    SUPPORT = "SUPPORT"
    GESTION = "GESTION"