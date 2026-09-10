#!/bin/bash

# Script pour démarrer le serveur DataAutomation

echo "======================================"
echo "Démarrage de DataAutomation"
echo "======================================"
echo ""

# Se déplacer dans le répertoire du projet
cd /home/lz-jihed/dataAutomation

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate

# Vérifier les migrations
echo "Vérification des migrations..."
python manage.py migrate

# Démarrer le serveur
echo ""
echo "======================================"
echo "Serveur démarré!"
echo "======================================"
echo ""
echo "Accès à l'application:"
echo "  - URL: http://127.0.0.1:8000/"
echo "  - Admin: http://127.0.0.1:8000/admin/"
echo ""
echo "Pour arrêter le serveur: Ctrl+C"
echo ""

python manage.py runserver 0.0.0.0:8000
