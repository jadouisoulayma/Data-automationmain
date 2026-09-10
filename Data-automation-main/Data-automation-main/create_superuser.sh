#!/bin/bash

# Script pour créer un super-utilisateur Django

echo "======================================"
echo "Création d'un super-utilisateur Django"
echo "======================================"
echo ""

cd /home/lz-jihed/dataAutomation
source venv/bin/activate
python manage.py createsuperuser

echo ""
echo "Super-utilisateur créé avec succès!"
echo "Utilisez ces identifiants pour:"
echo "  - Accéder à l'admin: http://127.0.0.1:8000/admin/"
echo "  - Vous connecter à l'app: http://127.0.0.1:8000/"
