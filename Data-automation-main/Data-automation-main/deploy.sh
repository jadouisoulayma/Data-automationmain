#!/bin/bash
echo "🚀 Déploiement DataAutomation sur VPS..."

VPS_IP="38.242.254.203"
VPS_USER="root"
VPS_PATH="/root/dataAutomation"
LOCAL_PATH="/home/lz-jihed/dataAutomation"

# Transférer les fichiers (exclure venv, __pycache__, db.sqlite3)
echo "📦 Transfert des fichiers..."
rsync -avz --exclude='venv' \
           --exclude='__pycache__' \
           --exclude='*.pyc' \
           --exclude='db.sqlite3' \
           --exclude='media/*' \
           --exclude='staticfiles' \
           --exclude='logs' \
           --progress \
           ${LOCAL_PATH}/ ${VPS_USER}@${VPS_IP}:${VPS_PATH}/

# Exécuter sur le serveur
echo "⚙️  Configuration sur le serveur..."
ssh ${VPS_USER}@${VPS_IP} << 'EOF'
cd /root/dataAutomation

# Activer l'environnement virtuel
source venv/bin/activate

# Installer/mettre à jour les dépendances
pip install -r requirements.txt

# Créer le dossier logs s'il n'existe pas
mkdir -p logs

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Appliquer les migrations
python manage.py migrate

# Redémarrer l'application avec PM2
pm2 restart dataautomation || pm2 start ecosystem.config.js

# Sauvegarder la configuration PM2
pm2 save

echo "✅ Déploiement terminé!"
pm2 status
EOF

echo ""
echo "✅ Déploiement terminé avec succès!"
echo "🌐 Application accessible sur: http://${VPS_IP}:8000"
echo "📊 Logs: ssh ${VPS_USER}@${VPS_IP} 'pm2 logs dataautomation'"
