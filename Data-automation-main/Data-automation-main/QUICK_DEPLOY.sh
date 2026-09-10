#!/bin/bash
# Guide rapide de déploiement sur VPS
# Exécuter ce script depuis votre machine locale

echo "🚀 Guide de déploiement DataAutomation sur VPS"
echo "=============================================="
echo ""

VPS_IP="38.242.254.203"
VPS_USER="root"
VPS_PATH="/root/dataAutomation"  # Changez si nécessaire

echo "📋 Étape 1: Synchronisation des fichiers de configuration"
echo ""
echo "Méthode 1 - Avec rsync:"
echo "  rsync -avz --progress config/settings.py requirements.txt start_prod.sh ecosystem.config.js setup_vps.sh $VPS_USER@$VPS_IP:$VPS_PATH/"
echo ""
echo "Méthode 2 - Avec git:"
echo "  git add ."
echo "  git commit -m 'Config production'"
echo "  git push"
echo "  ssh $VPS_USER@$VPS_IP 'cd $VPS_PATH && git pull'"
echo ""
echo "=============================================="
echo ""
echo "📋 Étape 2: Sur le VPS, exécutez ces commandes:"
echo ""
cat << 'COMMANDS'
ssh root@38.242.254.203

cd /root/dataAutomation  # Ou votre chemin

# Vérifier que les fichiers sont là
ls -la start_prod.sh ecosystem.config.js setup_vps.sh

# Rendre les scripts exécutables
chmod +x start_prod.sh setup_vps.sh

# Exécuter le setup
./setup_vps.sh

# Vérifier le statut
pm2 status
pm2 logs dataautomation

COMMANDS

echo ""
echo "=============================================="
echo "🌐 L'application sera accessible sur:"
echo "   http://$VPS_IP:8000"
echo "=============================================="
