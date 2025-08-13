# 📌 Epic CRM CLI Version — Gestion Commerciale, Gestion & Support
<img width="1920" height="520" alt="16903799358611_P12-02" src="https://github.com/user-attachments/assets/b60538da-1d34-4eb5-9d87-b7c417aaa775" />

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![SQLite](https://img.shields.io/badge/sqlite-lightblue.svg)
![Tests](https://img.shields.io/badge/tests-pytest-green.svg)
![Coverage](https://img.shields.io/badge/coverage-73%25-yellowgreen.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

---

## 🌟 Vue d'ensemble

**Epic CRM CLI** est une application **CRM modulaire** orientée **ligne de commande** (⭐ sans interface web) permettant de gérer :

* **Utilisateurs** avec rôles (*GESTION*, *COMMERCIAL*, *SUPPORT*),
* **Clients** (ajout, mise à jour, suivi),
* **Contrats** (montants, état signé/non signé, soldes),
* **Événements** (planification, affectation au support).

L'application inclut :

* **Sentry** pour la supervision et le suivi des erreurs en production,
* **Tests unitaires & couverture** avec `pytest` et `coverage`.

Aucune interface graphique n'est nécessaire : tout se pilote via **menus CLI ergonomiques**.

---

## ✨ Fonctionnalités principales

* 🔐 **Authentification** avec rôles et permissions métier et JWT.
* 👥 Gestion des **utilisateurs**, clients, contrats, événements.
* 🔍 **Filtres et recherches** dans les listings.
* 💡 **Validations partagées** (email, téléphone, etc.) dans `services/validations`.
* 📈 **Couverture de code** mesurable facilement (`coverage.py`).
* 🛠️ **Sentry** pour remonter les exceptions et erreurs critiques.
* 📅 **Seed** de données de démo (`seed.py`).

---

## 🔧 Prérequis

* Python **3.12+**
* `pip` et `venv`
* SQLite (par défaut)

---

## 🚀 Installation & Démarrage

### 1) Cloner le projet et créer l'environnement virtuel

```bash
git clone https://github.com/Youorus/epic-crm-cli-version-Python-.git
cd epic-crm-cli-version-Python-

python3 -m venv .venv
source .venv/bin/activate  # macOS / Linux
# .\.venv\Scripts\Activate.ps1  # Windows PowerShell
```

### 2) Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 💡 Configuration

Créez un fichier `.env` à la racine :

```env
# --- Application ---
DEBUG=True
SECRET_KEY=change-me

# --- Sentry ---
SENTRY_DNS="...."
SENTRY_ENABLE=1
SENTRY_DSN=<votre_dsn_sentry>
SENTRY_ENV=dev
SENTRY_RELEASE=local-dev
SENTRY_TRACES=0.0
SENTRY_PROFILES=0.0
SENTRY_DEBUG=1
```

**Initialiser la base SQLite** :

```bash
python sqlite/init_db.py
```

**(Optionnel)** Remplir avec des données de démo :

```bash
python seed.py
```

---

## 🔗 Sentry

Le projet intègre un module `utils/sentry_init.py` qui :

* Charge les variables d'environnement Sentry,
* Active la remontée des erreurs seulement si `SENTRY_ENABLE=1` et un DSN est fourni / entrer le votre depuis votre sentry
* Envoie les données d'erreurs et traces vers votre projet Sentry.

Pour tester :

```bash
python -m utils.sentry_init
```

---

## 🛠️ Utilisation de la CLI

Lancer le programme principal :

```bash
python -m cli.main
```

Naviguez dans les menus selon votre rôle (Commercial / Gestion / Support).

Les validations sont gérées par `services/validations` et `validators/`.

---

## 📊 Tests & Couverture

**Lancer les tests** :

```bash
pytest -q
```

**Mesurer la couverture** :

```bash
coverage run -m pytest
coverage report -m
coverage html && open htmlcov/index.html  # macOS
```

---

## 🛠️ Arborescence

```text
epic-crm-cli-version-Python-/
├─ cli/                  # Menus et formulaires CLI
├─ data/                 # Données locales / fixtures
├─ enums/                # Énumérations globales
├─ models/               # Modèles métier
├─ orm/                  # Mapping objet-relationnel
├─ security/             # Authentification & permissions
├─ services/             # Logique métier et validations partagées
├─ sqlite/               # Initialisation et gestion SQLite
├─ tests/                # Tests unitaires et d'intégration
├─ utils/                # Outils génériques (dont sentry_init.py)
├─ validators/           # Fonctions de validation réutilisables
├─ seed.py                # Script de peuplement de données
├─ requirements.txt       # Dépendances Python
├─ pytest.ini             # Configuration pytest
└─ .env                   # Variables d'environnement
```

---

## 📜 Licence

**MIT** — libre d'utilisation et de modification.

**Auteur :** Marc Takoumba
