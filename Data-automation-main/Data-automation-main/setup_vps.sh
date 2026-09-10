#!/bin/bash
# Script de configuration initiale sur le VPS
# À exécuter UNE SEULE FOIS lors du premier déploiement

echo "🔧 Configuration initiale du VPS pour DataAutomation..."

# Variables
PROJECT_PATH="/root/dataAutomation"

# Créer l'environnement virtuel
echo "📦 Création de l'environnement virtuel..."
python3 -m venv ${PROJECT_PATH}/venv

# Activer l'environnement virtuel
source ${PROJECT_PATH}/venv/bin/activate

# Installer les dépendances
echo "📥 Installation des dépendances..."
pip install --upgrade pip
pip install -r ${PROJECT_PATH}/requirements.txt

# Créer le dossier logs
echo "📁 Création du dossier logs..."
mkdir -p ${PROJECT_PATH}/logs

# Rendre le script de démarrage exécutable
chmod +x ${PROJECT_PATH}/start_prod.sh

# Collecter les fichiers statiques
echo "🎨 Collecte des fichiers statiques..."
python ${PROJECT_PATH}/manage.py collectstatic --noinput

# Appliquer les migrations
echo "🗄️  Application des migrations..."
python ${PROJECT_PATH}/manage.py migrate

# Créer le superuser
echo "👤 Création du superuser..."
python ${PROJECT_PATH}/manage.py createsuperuser

# Ajuster les permissions
echo "🔐 Ajustement des permissions..."
chmod -R 755 ${PROJECT_PATH}
chmod -R 777 ${PROJECT_PATH}/media

# Démarrer avec PM2
echo "🚀 Démarrage de l'application avec PM2..."
pm2 start ${PROJECT_PATH}/ecosystem.config.js

# Sauvegarder la configuration PM2
pm2 save

# Configurer PM2 pour démarrer au boot
echo "⚙️  Configuration du démarrage automatique PM2..."
pm2 startup

echo ""
echo "✅ Configuration initiale terminée!"
echo ""
echo "⚠️  IMPORTANT: Copiez et exécutez la commande pm2 startup affichée ci-dessus"
echo ""
echo "📊 Status de l'application:"
pm2 status

echo ""
echo "🌐 Application accessible sur: http://38.242.254.203:8000"
echo "📊 Voir les logs: pm2 logs dataautomation"
