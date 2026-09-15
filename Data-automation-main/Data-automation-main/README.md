# DataAutomation — Plateforme d'automatisation Python

## 📋 Description

DataAutomation est une plateforme web Django qui permet aux utilisateurs de créer, modifier et exécuter des scripts Python, avec un **pipeline produits automatisé** dédié à PrestaShop / High-Tech Moving : du fichier stock brut à l'Excel final importable, sans coder.

---

## ✨ Fonctionnalités

### 🔐 Authentification & Utilisateurs
- Authentification sécurisée (login uniquement — pas d'auto-inscription)
- Gestion multi-utilisateurs avec espace de travail isolé par utilisateur
- L'administrateur crée les comptes via le panel Django admin

### 🐍 Scripts Python
- Création, édition et suppression de scripts Python
- Variables par défaut configurables à la création
- Variables dynamiques injectées à chaque exécution
- Exécution en temps réel avec terminal SSE (Server-Sent Events)
- Upload de fichiers Excel avant exécution

### 📊 Excel & Données
- Support Excel complet (`.xlsx`, `.xls`)
- Explorateur Excel avancé (100 % client-side, sans stockage serveur) :
  - Navigation multi-feuilles
  - Édition de cellules (double-clic)
  - Filtres avancés (12 opérateurs)
  - Regroupement avec agrégations (somme, moyenne, min, max, count)
  - Export Excel/CSV des données filtrées

### 🏭 Pipeline Produits (module principal)
Pipeline automatisé en **10 étapes**, regroupées en **4 grandes phases** :

| Phase | Étapes |
|---|---|
| **Préparation** | Nettoyage & fusion, Contrôle qualité, Comparaison backoffice, Mapping état |
| **Contrôle** | Correction EAN-13 |
| **Enrichissement** | Prédiction ML (marque + catégorie), Textes SEO, Prix & SKU, Images |
| **Export** | Export Excel (4 fichiers) + rapport JSON |

**Fichiers générés par exécution :**
- `YYYY-MM-DD_HH.MM.SS_produits_finaux.xlsx`
- `YYYY-MM-DD_HH.MM.SS_lignes_avec_erreurs.xlsx`
- `YYYY-MM-DD_HH.MM.SS_produits_dupliques.xlsx`
- `YYYY-MM-DD_HH.MM.SS_produits_non_dupliques.xlsx`
- `YYYY-MM-DD_HH.MM.SS_rapport.json`

**Système FIFO :**
- 3 dernières exécutions conservées dans `media/workflow/resultats/`
- 3 derniers fichiers dans `media/workflow/inputs/` et `media/workflow/backoffice/`
- Fichier d'entraînement ML fixe côté backend : `script data/entrainementdataset.csv`

**Reporting par exécution :**
- Dashboard avec 6 KPIs (produits traités, erreurs, dupliqués, durée, vitesse)
- Jauge SVG de conformité
- Chronologie d'exécution (4 phases horodatées)
- Catégories d'erreurs de saisie (champ vide, valeur = 0, valeur négative, non numérique)
- Tableau filtrable des lignes avec erreurs
- Liens de téléchargement des 4 fichiers Excel

### 📁 Gestion de Fichiers Admin
- Import et gestion de fichiers projet (modèles, `.env`, configs)
- Types : Modèle, Environnement, Configuration, Template, Autre
- Formats supportés : Excel, CSV, JSON, XML, PDF, Python, SQL, etc.
- Audit complet (utilisateur + date d'import)

### 📜 Historique
- 3 dernières exécutions affichées dans l'interface
- Statut, progression, produits traités, actions disponibles
- Bouton **Reporting** (📊) par exécution terminée avec succès

---

## 🛠️ Technologies

### Backend
- **Django 5.1.3** — framework web Python
- **SQLite** — base de données intégrée (dev)
- **Python 3.12** — langage principal
- **pandas 2.3.3** — traitement des données
- **openpyxl 3.1.5** — lecture/écriture Excel
- **scikit-learn** — prédiction ML (marque + catégorie)
- **gunicorn 23.0.0** — serveur WSGI production
- **whitenoise 6.8.2** — service des fichiers statiques

### Frontend
- **Bootstrap 5.3** — framework CSS responsive
- **Bootstrap Icons** — icônes
- **XLSX.js** — traitement Excel côté client (explorateur)

### Temps réel
- **Server-Sent Events (SSE)** — streaming des logs d'exécution
- **Threading Python** — pipeline exécuté en arrière-plan

---

## 📦 Installation

### Prérequis
- Python 3.12+
- pip
- virtualenv

### Démarrage rapide

```bash
# 1. Activer l'environnement virtuel
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux / Mac

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Appliquer les migrations
python manage.py migrate

# 4. Créer un super-utilisateur
python manage.py createsuperuser

# 5. Lancer le serveur
python manage.py runserver
```

Accès : http://127.0.0.1:8000/

---

## 👤 Gestion des utilisateurs

Seul l'administrateur peut créer des utilisateurs :
1. Connectez-vous à http://127.0.0.1:8000/admin/
2. Allez dans **Users** → **Add user**
3. Remplissez les informations et sauvegardez

---

## 📝 Utilisation du Pipeline Produits

### Fichiers requis
| Fichier | Description |
|---|---|
| `input.xlsx` | Fichier stock brut (nom_produit, ean, etat, pc, prix_vente, quantite) |
| `databackoffice.csv` | Produits déjà en ligne (name, ean13) — comparaison étape 4 |
| `entrainementdataset.csv` | Dataset ML — **fixe côté backend**, non uploadable |

### Lancer une exécution
1. Aller sur **Pipeline Produits** dans le menu
2. Déposer `input.xlsx` et `databackoffice.csv` (ou utiliser les fichiers par défaut)
3. Cliquer sur **Lancer le pipeline**
4. Suivre la progression en temps réel (10 étapes)
5. Télécharger les 4 fichiers Excel depuis l'historique
6. Consulter le **Reporting** pour les statistiques détaillées

---

## 📁 Structure du projet

```
Data-automation-main/
├── config/                         # Configuration Django
│   ├── settings.py                 # Paramètres (DB, apps, middleware)
│   ├── urls.py                     # URLs racine
│   ├── asgi.py
│   └── wsgi.py
│
├── scripts/                        # Application principale
│   ├── models.py                   # Modèles : Script, ScriptExecution, AdminFile, ProductWorkflow
│   ├── views.py                    # Toutes les vues (scripts + pipeline produits)
│   ├── urls.py                     # Routes URL
│   ├── admin.py                    # Configuration panel admin Django
│   ├── apps.py                     # ✨ NOUVEAU — AppConfig + FIFO au démarrage
│   ├── fifo.py                     # ✨ NOUVEAU — Rotation FIFO (inputs, backoffice, resultats)
│   ├── product_pipeline.py         # ✨ NOUVEAU — Pipeline 10 étapes (nettoyage → export)
│   ├── tests.py
│   ├── __init__.py                 # ✨ MIS À JOUR — enregistre ScriptsConfig
│   ├── migrations/                 # Migrations de base de données
│   └── templatetags/
│       ├── __init__.py
│       └── script_filters.py       # Filtres Django (basename, split)
│
├── templates/
│   ├── base.html                   # Template de base (navbar, Bootstrap)
│   └── scripts/
│       ├── login.html
│       ├── dashboard.html
│       ├── script_form.html
│       ├── script_detail.html
│       ├── script_confirm_delete.html
│       ├── script_execute.html
│       ├── execution_realtime.html
│       ├── execution_detail.html
│       ├── execution_history.html
│       ├── excel_explorer.html
│       ├── admin_files.html
│       ├── workflow_produits.html      # ✨ NOUVEAU — Formulaire pipeline + historique
│       ├── workflow_progress.html      # ✨ NOUVEAU — Suivi temps réel (SSE)
│       ├── workflow_detail.html        # ✨ NOUVEAU — Détail d'une exécution
│       ├── workflow_confirm_delete.html# ✨ NOUVEAU — Confirmation suppression
│       └── workflow_reporting.html     # ✨ NOUVEAU — Dashboard reporting (stats, erreurs, temps)
│
├── media/
│   └── workflow/                   # ✨ NOUVEAU — Stockage pipeline produits
│       ├── inputs/                 # Fichiers stock uploadés (nommés YYYY-MM-DD_HH.MM.SS.xlsx)
│       ├── backoffice/             # Fichiers backoffice uploadés (nommés par date)
│       ├── training/               # (vide — fichier ML fixe dans script data/)
│       ├── outputs/                # (vide — remplacé par resultats/)
│       └── resultats/              # ✨ NOUVEAU — 4 fichiers + rapport JSON par exécution
│           └── YYYY-MM-DD_HH.MM.SS/
│               ├── YYYY-MM-DD_HH.MM.SS_produits_finaux.xlsx
│               ├── YYYY-MM-DD_HH.MM.SS_lignes_avec_erreurs.xlsx
│               ├── YYYY-MM-DD_HH.MM.SS_produits_dupliques.xlsx
│               ├── YYYY-MM-DD_HH.MM.SS_produits_non_dupliques.xlsx
│               └── YYYY-MM-DD_HH.MM.SS_rapport.json
│
├── script data/                    # ✨ NOUVEAU — Fichiers par défaut du pipeline
│   ├── input.xlsx                  # Fichier stock par défaut
│   ├── databackoffice.csv          # Backoffice par défaut
│   └── entrainementdataset.csv     # Dataset ML fixe (non uploadable)
│
├── static/                         # Fichiers statiques (CSS, JS, Bootstrap)
├── venv/                           # Environnement virtuel Python
├── manage.py                       # Script de gestion Django
├── requirements.txt                # Dépendances Python
├── db.sqlite3                      # Base de données SQLite
├── README.md                       # Ce fichier
├── DEPLOYMENT.md                   # Guide de déploiement VPS
├── ecosystem.config.js             # Config PM2 (production)
├── deploy.sh                       # Script de déploiement
├── start_server.sh                 # Démarrage serveur développement
└── create_superuser.sh             # Création premier admin
```

---

## 🗄️ Modèles de données

### Script
Script Python créé par un utilisateur.

| Champ | Type | Description |
|---|---|---|
| `name` | CharField(200) | Nom du script |
| `description` | TextField | Description (optionnel) |
| `code` | TextField | Code Python |
| `default_variables` | JSONField | Variables par défaut `{"NOM": "valeur"}` |
| `user` | ForeignKey(User) | Propriétaire |
| `created_at` | DateTimeField | Date de création (auto) |
| `updated_at` | DateTimeField | Dernière modification (auto) |

### ScriptExecution
Historique d'exécution d'un script.

| Champ | Type | Description |
|---|---|---|
| `script` | ForeignKey(Script) | Script exécuté |
| `user` | ForeignKey(User) | Utilisateur |
| `status` | CharField | `pending` / `running` / `success` / `error` |
| `logs` | TextField | Logs de sortie |
| `input_file` | FileField | Fichier d'entrée uploadé (optionnel) |
| `output_file` | FileField | Fichier de sortie généré (optionnel) |
| `variables` | JSONField | Variables utilisées |
| `executed_at` | DateTimeField | Date/heure d'exécution (auto) |

### AdminFile
Fichiers partagés (modèles, configs).

| Champ | Type | Description |
|---|---|---|
| `name` | CharField(200) | Nom descriptif |
| `description` | TextField | Description (optionnel) |
| `file` | FileField | Fichier uploadé |
| `file_type` | CharField | `model` / `env` / `config` / `template` / `other` |
| `file_size` | BigIntegerField | Taille en octets (auto) |
| `uploaded_by` | ForeignKey(User) | Utilisateur |
| `uploaded_at` | DateTimeField | Date d'import (auto) |

### ProductWorkflow ✨ NOUVEAU
Exécution du pipeline produits.

| Champ | Type | Description |
|---|---|---|
| `user` | ForeignKey(User) | Utilisateur |
| `status` | CharField | `pending` / `running` / `success` / `error` |
| `progress` | IntegerField | Progression 0–100 |
| `progress_message` | CharField(300) | Message d'étape en cours |
| `input_file` | FileField | Fichier stock uploadé (`workflow/inputs/`) |
| `backoffice_file` | FileField | Fichier backoffice uploadé (`workflow/backoffice/`) |
| `training_file` | FileField | Fichier ML (toujours vide — fichier fixe) |
| `output_file` | FileField | Produits finaux (`workflow/outputs/`) |
| `output_erreurs_file` | FileField | Lignes avec erreurs |
| `output_dupliques_file` | FileField | Produits dupliqués |
| `output_non_dupliques_file` | FileField | Produits non dupliqués |
| `logs` | TextField | Logs d'exécution |
| `nb_lignes_output` | IntegerField | Nombre de produits traités |
| `created_at` | DateTimeField | Date de création (auto) |
| `finished_at` | DateTimeField | Date de fin (auto) |

---

## 🔄 Système FIFO

La rotation automatique est appliquée :
- **Au démarrage du serveur** (`AppConfig.ready()` dans `apps.py`)
- **Après chaque exécution** (succès ou erreur)

| Répertoire | Limite | Critère |
|---|---|---|
| `media/workflow/inputs/` | 3 fichiers | Date de modification |
| `media/workflow/backoffice/` | 3 fichiers | Date de modification |
| `media/workflow/resultats/` | 3 sous-dossiers | Ordre alphabétique (= chronologique) |
| Base de données `ProductWorkflow` | 3 enregistrements | Date de création |

---

## 🔒 Sécurité

- Authentification obligatoire (`@login_required` sur toutes les vues)
- Pas d'auto-inscription
- Isolation des fichiers et exécutions par utilisateur
- Validation des fichiers requis avant création du workflow en base
- Timeout d'exécution des scripts Python

---

## 🚀 Déploiement

### Développement
```bash
venv\Scripts\activate
python manage.py runserver
```

### Production (VPS / Gunicorn + Nginx)

1. Modifier `config/settings.py` :
   - `DEBUG = False`
   - `ALLOWED_HOSTS = ['votre-ip', 'votre-domaine.com']`
   - `SECRET_KEY` depuis variable d'environnement

2. Collecter les fichiers statiques :
```bash
python manage.py collectstatic
```

3. Lancer avec Gunicorn :
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

4. Consulter `DEPLOYMENT.md` pour la configuration complète Nginx + PM2.

---

## 📊 Routes URL

| URL | Vue | Description |
|---|---|---|
| `/` | `dashboard` | Tableau de bord |
| `/login/` | `login_view` | Connexion |
| `/workflow-produits/` | `workflow_produits` | Pipeline produits |
| `/workflow-produits/run/` | `workflow_produits_run` | Lancer le pipeline |
| `/workflow-produits/<pk>/progress/` | `workflow_produits_progress` | Suivi temps réel |
| `/workflow-produits/<pk>/status/` | `workflow_produits_status` | API JSON polling |
| `/workflow-produits/<pk>/` | `workflow_produits_detail` | Détail exécution |
| `/workflow-produits/<pk>/reporting/` | `workflow_produits_reporting` | Dashboard reporting |
| `/workflow-produits/<pk>/download/` | `workflow_produits_download` | Télécharger produits finaux |
| `/workflow-produits/<pk>/download/erreurs/` | — | Télécharger lignes erreurs |
| `/workflow-produits/<pk>/download/dupliques/` | — | Télécharger dupliqués |
| `/workflow-produits/<pk>/download/non-dupliques/` | — | Télécharger non dupliqués |
| `/workflow-produits/<pk>/delete/` | `workflow_produits_delete` | Supprimer |
| `/excel-explorer/` | `excel_explorer` | Explorateur Excel |
| `/admin-files/` | `admin_files` | Fichiers admin |

---

## 📄 Licence

Ce projet est développé pour un usage interne — High-Tech Moving.

---

**Développé avec ❤️ en Django 5.1.3 | Python 3.12 | Bootstrap 5.3**
