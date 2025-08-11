# config.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)   # <-- crée le dossier si besoin

DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'app.db')}"  # ex: sqlite:////Users/.../PythonProject2/data/app.db