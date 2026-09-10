#!/bin/bash
# Installation de Python 3.12 sur Ubuntu/Debian
# À exécuter sur le VPS

echo "🐍 Installation de Python 3.12 sur le VPS..."

# Vérifier la version actuelle de Python
echo "📌 Version Python actuelle:"
python3 --version

# Ajouter le dépôt deadsnakes pour Python 3.12
echo "📦 Ajout du dépôt deadsnakes..."
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update

# Installer Python 3.12
echo "📥 Installation de Python 3.12..."
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Installer pip pour Python 3.12
echo "📥 Installation de pip..."
sudo apt install -y python3-pip
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# Vérifier l'installation
echo ""
echo "✅ Vérification de l'installation:"
python3.12 --version
python3.12 -m pip --version

echo ""
echo "✅ Python 3.12 installé avec succès!"
