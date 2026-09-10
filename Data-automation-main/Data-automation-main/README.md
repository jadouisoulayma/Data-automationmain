# DataAutomation - Plateforme d'automatisation Python

## 📋 Description

DataAutomation est une plateforme web similaire à Google Colab qui permet aux utilisateurs de créer, modifier et exécuter des scripts Python avec gestion des fichiers Excel en entrée/sortie, affichage en temps réel, et outils avancés de manipulation de données.

## ✨ Fonctionnalités

### 🔐 Authentification & Utilisateurs
- **Authentification sécurisée**: Login uniquement (pas d'auto-inscription, l'admin crée les utilisateurs)
- **Gestion multi-utilisateurs**: Chaque utilisateur a son propre espace de travail

### 🐍 Scripts Python
- **Création et modification**: Interface intuitive pour écrire du code Python
- **Variables personnalisées**: Définir des variables par défaut lors de la création du script
- **Variables d'exécution**: Ajouter des variables dynamiques à chaque exécution
- **Exécution en temps réel**: Terminal interactif affichant les logs au fur et à mesure (SSE)
- **Upload de fichiers**: Importer des fichiers Excel en entrée avant l'exécution

### 📊 Excel & Données
- **Support Excel complet**: Input/Output avec fichiers Excel (.xlsx, .xls)
- **Explorateur Excel avancé**: 
  - Import de fichiers Excel sans stockage (100% client-side)
  - Visualisation multi-feuilles avec onglets
  - Édition de cellules (double-clic)
  - Numérotation automatique des lignes
  - Sélection de lignes et colonnes
  - Filtres avancés (12 opérateurs: égal, contient, supérieur, etc.)
  - Recherche et tri
  - Regroupement avec agrégations (somme, moyenne, min, max, compte)
  - Export Excel/CSV des données filtrées uniquement
  - Statistiques en temps réel (lignes, colonnes, nom de feuille)

### 📁 Gestion de Fichiers Admin
- **Stockage de fichiers projet**: Importer et gérer des modèles de données, fichiers .env, configurations
- **Types de fichiers**: Modèle de données, Environnement, Configuration, Template, Autre
- **Formats supportés**: Excel, Word, Text, PDF, JSON, XML, CSV, Python, SQL, etc.
- **Audit complet**: Utilisateur et date d'import enregistrés
- **Actions**: Télécharger, supprimer avec confirmation
- **Affichage taille**: Taille lisible (octets, Ko, Mo, Go)

### 📜 Historique & Logs
- **Historique complet**: Toutes les exécutions conservées avec logs
- **Affichage détaillé**: Statut, utilisateur, date, logs, fichiers
- **Téléchargement**: Accès aux fichiers input/output des exécutions
- **Système FIFO**: Stockage limité (5 fichiers/script, 100 total) avec logs illimités

## 🛠️ Technologies

### Backend
- **Django 6.0**: Framework web Python
- **SQLite**: Base de données intégrée
- **Python 3.12**: Langage de programmation

### Frontend
- **Bootstrap 5.3**: Framework CSS responsive
- **Bootstrap Icons**: Bibliothèque d'icônes
- **jQuery 3.7.0**: Manipulation DOM
- **DataTables 1.13.6**: Tables interactives avec tri/filtrage/pagination
- **XLSX.js 0.18.5**: Traitement Excel côté client

### Traitement de données
- **pandas 2.3.3**: Analyse et manipulation de données
- **openpyxl 3.1.5**: Lecture/écriture Excel

### Temps réel
- **Server-Sent Events (SSE)**: Streaming des logs d'exécution en temps réel
- **subprocess.Popen()**: Exécution non-bloquante des scripts Python

## 📦 Installation

### Prérequis

- Python 3.12 ou supérieur
- pip
- virtualenv

### Installation rapide avec scripts

Le projet inclut des scripts pour simplifier le démarrage:

1. **Créer le super-utilisateur** (première fois):
```bash
./create_superuser.sh
```

2. **Démarrer le serveur**:
```bash
./start_server.sh
```

3. **Accéder à l'application**:
- Application: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

### Installation manuelle

1. **Cloner le projet**:
```bash
cd /home/lz-jihed/dataAutomation
```

2. **Créer et activer l'environnement virtuel**:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**:
```bash
pip install -r requirements.txt
```

4. **Appliquer les migrations**:
```bash
python manage.py migrate
```

5. **Créer un super-utilisateur** (admin):
```bash
python manage.py createsuperuser
```

6. **Lancer le serveur**:
```bash
python manage.py runserver
```

## 👤 Gestion des utilisateurs

### Création d'utilisateurs

Seul l'administrateur peut créer des utilisateurs:

1. Connectez-vous à l'interface admin: http://127.0.0.1:8000/admin/
2. Allez dans "Users"
3. Cliquez sur "Add user"
4. Remplissez les informations et sauvegardez

Les utilisateurs pourront ensuite se connecter avec leurs identifiants sur la page de login.

## 📝 Utilisation

### 1. Créer un script avec variables par défaut

1. Connectez-vous à l'application
2. Cliquez sur "Nouveau script"
3. Donnez un nom et une description
4. Définissez des variables par défaut (optionnel):
   - Exemple: `DB_HOST`, `API_KEY`, `OUTPUT_FORMAT`
5. Écrivez votre code Python
6. Sauvegardez

### 2. Exécuter un script

1. Cliquez sur un script dans le tableau de bord
2. Cliquez sur "Exécuter"
3. Remplissez les valeurs des variables (si définies)
4. Uploadez un fichier Excel si nécessaire (optionnel)
5. Cliquez sur "Lancer l'exécution"
6. **Visualisation temps réel**: Les logs s'affichent au fur et à mesure dans un terminal
7. Téléchargez le fichier de résultat une fois terminé

### 3. Utiliser l'Explorateur Excel

1. Accédez à "Explorateur Excel" dans le menu
2. Glissez-déposez un fichier Excel ou cliquez pour l'importer
3. **Visualiser**: Navigation multi-feuilles, statistiques
4. **Éditer**: Double-cliquez sur une cellule pour modifier
5. **Sélectionner**: Cliquez sur les numéros de ligne ou en-têtes de colonne
6. **Filtrer**: 
   - Recherche simple dans la barre
   - Filtres avancés avec 12 opérateurs
7. **Regrouper**: Choisir colonne + fonction d'agrégation
8. **Exporter**: Excel ou CSV (uniquement les données filtrées)
9. Aucun fichier n'est stocké sur le serveur

### 4. Gérer les fichiers admin

1. Accédez à "Fichiers Admin" dans le menu
2. Cliquez sur "Importer un fichier"
3. Remplissez le formulaire:
   - Nom du fichier
   - Type (Modèle, Env, Config, Template, Autre)
   - Description (optionnel)
   - Sélectionner le fichier
4. Les fichiers sont accessibles à tous les utilisateurs
5. Actions: Télécharger ou supprimer

### Exemple de script avec fichier Excel et variables

```python
import pandas as pd
import os

# Récupérer les variables d'environnement personnalisées
db_host = os.environ.get('DB_HOST', 'localhost')
output_format = os.environ.get('OUTPUT_FORMAT', 'excel')

# Lire le fichier d'entrée (Excel)
input_file = os.environ.get('INPUT_FILE', 'input.xlsx')
df = pd.read_excel(input_file)

print(f"Connexion à: {db_host}")
print(f"Lignes lues: {len(df)}")

# Traiter les données
df['Total'] = df['Prix'] * df['Quantité']
df['TVA'] = df['Total'] * 0.20

# Sauvegarder selon le format demandé
if output_format == 'csv':
    df.to_csv('output.csv', index=False)
    print("Résultat sauvegardé en CSV")
else:
    df.to_excel('output.xlsx', index=False)
    print("Résultat sauvegardé en Excel")

print(f"Total général: {df['Total'].sum():.2f} €")
```

### Variables d'environnement disponibles

Variables système injectées automatiquement:
- `INPUT_FILE`: Chemin vers le fichier d'entrée uploadé (si fourni)

Variables personnalisées:
- Toutes les variables définies lors de l'exécution sont disponibles via `os.environ.get('NOM_VARIABLE')`
- Les variables par défaut du script sont pré-remplies (modifiables à chaque exécution)

### Générer un fichier de sortie

Pour que votre script génère un fichier téléchargeable:
- Créez un fichier nommé `output.xlsx` (ou `output.csv`, `output.txt`, etc.) dans le répertoire courant
- Il sera automatiquement détecté, sauvegardé et disponible au téléchargement
- Le nom du fichier peut être dynamique mais doit commencer par `output`

## 📊 Système de gestion du stockage

Pour optimiser l'espace disque tout en conservant l'historique complet:

- ✅ **Exécutions illimitées** : Tous les logs et historiques sont conservés
- 💾 **Fichiers limités** : Maximum 5 fichiers par script
- 💾 **Limite globale** : Maximum 100 fichiers totaux dans le projet
- 🗑️ Les vieux fichiers (input/output) sont automatiquement supprimés
- 📝 Les logs d'exécution restent accessibles même après suppression des fichiers
- Système **FIFO** : Les fichiers les plus anciens sont supprimés en premier

## 🔒 Sécurité

- Authentification obligatoire pour accéder à l'application
- Timeout de 5 minutes pour l'exécution des scripts
- Isolation des exécutions par utilisateur
- Pas d'auto-inscription (sécurité renforcée)

## 📁 Structure du projet

```
dataAutomation/
├── config/                 # Configuration Django
│   ├── settings.py        # Paramètres (DB, apps, middleware)
│   ├── urls.py            # URLs racine
│   └── wsgi.py            # Point d'entrée WSGI
├── scripts/                # Application principale
│   ├── models.py          # Modèles: Script, ScriptExecution, AdminFile
│   ├── views.py           # Vues et logique métier
│   ├── admin.py           # Configuration admin Django
│   ├── urls.py            # Routes URL
│   └── migrations/        # Migrations de base de données
├── templates/              # Templates HTML
│   ├── base.html          # Template de base avec navbar
│   └── scripts/
│       ├── login.html              # Page de connexion
│       ├── dashboard.html          # Tableau de bord principal
│       ├── script_form.html        # Création/édition de script
│       ├── script_detail.html      # Détails d'un script
│       ├── script_execute.html     # Formulaire d'exécution
│       ├── execution_realtime.html # Terminal temps réel (SSE)
│       ├── execution_detail.html   # Détails d'une exécution
│       ├── execution_history.html  # Historique des exécutions
│       ├── excel_explorer.html     # Explorateur Excel avancé
│       └── admin_files.html        # Gestion fichiers admin
├── static/                 # Fichiers statiques CSS/JS (Bootstrap, icons)
├── media/                  # Fichiers uploadés (séparés par type)
│   ├── inputs/            # Fichiers d'entrée des exécutions
│   ├── outputs/           # Fichiers de sortie des exécutions
│   └── admin_files/       # Fichiers admin (modèles, configs, etc.)
├── venv/                   # Environnement virtuel Python
├── manage.py               # Script de gestion Django
├── requirements.txt        # Dépendances Python
├── db.sqlite3             # Base de données SQLite
├── start_server.sh        # Script de démarrage rapide
├── create_superuser.sh    # Script de création admin
└── README.md              # Documentation
```

## 🗄️ Modèles de données

### Script
Représente un script Python créé par un utilisateur.

**Champs:**
- `name`: Nom du script (CharField, 200 caractères max)
- `description`: Description du script (TextField, optionnel)
- `code`: Code Python (TextField)
- `default_variables`: Variables par défaut (JSONField, dict) - Ex: `{"DB_HOST": "", "API_KEY": ""}`
- `user`: Propriétaire du script (ForeignKey → User)
- `created_at`: Date de création (DateTimeField, auto)
- `updated_at`: Dernière modification (DateTimeField, auto)

**Relations:**
- `executions`: Liste des exécutions (reverse ForeignKey)

### ScriptExecution
Historique d'exécution d'un script.

**Champs:**
- `script`: Script exécuté (ForeignKey → Script)
- `user`: Utilisateur qui a lancé l'exécution (ForeignKey → User)
- `status`: Statut d'exécution (CharField) - Choix: pending, running, success, error
- `logs`: Logs de sortie du script (TextField)
- `input_file`: Fichier d'entrée uploadé (FileField, optionnel)
- `output_file`: Fichier de sortie généré (FileField, optionnel)
- `variables`: Variables utilisées (JSONField, dict) - Ex: `{"DB_HOST": "localhost", "API_KEY": "abc123"}`
- `executed_at`: Date/heure d'exécution (DateTimeField, auto)

**Méthodes:**
- `get_input_filename()`: Retourne le nom du fichier d'entrée
- `get_output_filename()`: Retourne le nom du fichier de sortie
- `save()`: Override pour gérer le système FIFO (max 5 fichiers/script, 100 total)

### AdminFile
Fichiers de configuration et modèles partagés.

**Champs:**
- `name`: Nom descriptif du fichier (CharField, 200 caractères)
- `description`: Description du fichier (TextField, optionnel)
- `file`: Fichier uploadé (FileField)
- `file_type`: Type de fichier (CharField) - Choix: model, env, config, template, other
- `file_size`: Taille en octets (BigIntegerField, auto)
- `uploaded_by`: Utilisateur ayant importé (ForeignKey → User)
- `uploaded_at`: Date d'import (DateTimeField, auto)
- `updated_at`: Dernière modification (DateTimeField, auto)

**Méthodes:**
- `get_filename()`: Retourne le nom de base du fichier
- `get_file_size_display()`: Retourne la taille lisible (Ko, Mo, Go)
- `save()`: Override pour calculer automatiquement la taille du fichier
- `delete()`: Override pour supprimer le fichier physique du disque

## 🚀 Déploiement

### Développement
Le projet est prêt à l'emploi en mode développement:
```bash
./start_server.sh
```

### Production (VPS)

Le projet inclut un script de déploiement pour VPS:

1. **Préparer le VPS**:
   - IP: 38.242.254.203
   - Python 3.12+, pip, virtualenv installés
   - Nginx et Gunicorn configurés

2. **Déployer**:
```bash
./deploy_38.242.254.203.sh
```

3. **Configuration production**:
   - Modifier `DEBUG = False` dans `config/settings.py`
   - Définir `ALLOWED_HOSTS = ['38.242.254.203', 'votre-domaine.com']`
   - Utiliser PostgreSQL au lieu de SQLite (recommandé)
   - Configurer Nginx comme reverse proxy
   - Utiliser Gunicorn comme serveur WSGI
   - Variables d'environnement pour `SECRET_KEY` et autres secrets
   - Activer HTTPS avec Let's Encrypt

4. **Sécurité**:
   - Fichiers media et static servis par Nginx
   - CSRF et session cookies sécurisés
   - Timeout d'exécution des scripts (5 minutes)
   - Isolation des fichiers par utilisateur

### Scripts de déploiement disponibles
- `start_server.sh`: Démarrage serveur de développement
- `create_superuser.sh`: Création du premier admin
- `deploy_38.242.254.203.sh`: Déploiement automatique sur VPS

## 📞 Support & Contribution

### Repository GitHub
- **URL**: https://github.com/jihedloulizi/dataAutomation
- **Branche**: main
- **Développeur**: jihedloulizi

### Support
Pour toute question ou problème:
- Ouvrir une issue sur GitHub
- Contacter l'administrateur système
- Consulter la documentation Django: https://docs.djangoproject.com/

### Fonctionnalités complètes
✅ Authentification utilisateurs (login only)  
✅ CRUD scripts Python avec éditeur de code  
✅ Variables personnalisées (par défaut + runtime)  
✅ Exécution temps réel avec terminal SSE  
✅ Upload/Download fichiers Excel  
✅ Historique complet des exécutions  
✅ Explorateur Excel avancé (client-side)  
✅ Gestion fichiers admin (modèles, configs)  
✅ Système FIFO intelligent  
✅ Interface Bootstrap responsive  
✅ Panel admin Django  
✅ Scripts de déploiement  

### Statistiques du projet
- **Langage**: Python (Django 6.0)
- **Base de données**: SQLite (dev) / PostgreSQL (prod)
- **Temps réel**: Server-Sent Events
- **Interface**: Bootstrap 5.3 + DataTables + XLSX.js
- **Timezone**: Africa/Tunis
- **Langue**: Français (fr-fr)

## 📄 Licence

Ce projet est développé pour un usage interne.

---

**Développé avec ❤️ en Django 6.0 | Python 3.12 | Bootstrap 5.3**
