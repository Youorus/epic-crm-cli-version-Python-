# security/passwords.py
from __future__ import annotations
import os, hmac, hashlib

# Générer un sel aléatoire à la création de compte
def make_salt(n: int = 16) -> bytes:
    return os.urandom(n)

def hash_password(plain: str, salt: bytes) -> bytes:
    return hashlib.scrypt(plain.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=64)

def verify_password(plain: str, salt: bytes, hash_bytes: bytes) -> bool:
    dk = hash_password(plain, salt)
    return hmac.compare_digest(dk, hash_bytes)