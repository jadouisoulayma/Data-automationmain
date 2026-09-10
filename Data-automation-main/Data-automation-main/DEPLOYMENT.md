# Guide de Déploiement - DataAutomation

## 📋 Prérequis

Sur votre VPS (38.242.254.203), vous devez avoir installé:
- Python 3.12
- Node.js et npm
- PM2 (`npm install -g pm2`)
- Git

## 🚀 Déploiement Initial

### 1. Sur le VPS (première fois)

```bash
# Connexion SSH
ssh root@38.242.254.203

# Installation des dépendances
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git nodejs npm
sudo npm install -g pm2

# Créer le dossier du projet
mkdir -p /root/dataAutomation
```

### 2. Depuis votre machine locale

```bash
# Rendre le script de déploiement exécutable
chmod +x deploy.sh

# Lancer le déploiement
./deploy.sh
```

### 3. Configuration initiale sur le VPS (première fois seulement)

```bash
ssh root@38.242.254.203

cd /root/dataAutomation

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Créer le superuser
python manage.py createsuperuser

# Créer le dossier logs
mkdir -p logs

# Rendre le script de démarrage exécutable
chmod +x start_prod.sh

# Démarrer avec PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
# Copier et exécuter la commande affichée

# Configurer le firewall
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

## 🔄 Déploiements suivants

Simplement exécuter depuis votre machine locale:

```bash
./deploy.sh
```

## 📊 Gestion de l'application

### Commandes PM2 utiles

```bash
# Voir le statut
pm2 status

# Voir les logs
pm2 logs dataautomation

# Redémarrer l'application
pm2 restart dataautomation

# Arrêter l'application
pm2 stop dataautomation

# Monitoring en temps réel
pm2 monit
```

### Accès à l'application

- **Application**: http://38.242.254.203:8000
- **Admin**: http://38.242.254.203:8000/admin

### Logs

Les logs sont disponibles dans `/root/dataAutomation/logs/`:
- `gunicorn-access.log` - Logs d'accès Gunicorn
- `gunicorn-error.log` - Logs d'erreur Gunicorn
- `pm2-out.log` - Logs de sortie PM2
- `pm2-error.log` - Logs d'erreur PM2

```bash
# Voir les logs Gunicorn
tail -f logs/gunicorn-access.log
tail -f logs/gunicorn-error.log

# Voir les logs PM2
pm2 logs dataautomation
```

## 🔧 Dépannage

### L'application ne démarre pas

```bash
# Vérifier les logs
pm2 logs dataautomation

# Vérifier que l'environnement virtuel existe
ls -la /root/dataAutomation/venv

# Réinstaller l'environnement virtuel
cd /root/dataAutomation
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pm2 restart dataautomation
```

### Erreur 502 Bad Gateway

```bash
# Vérifier que l'application tourne
pm2 status

# Redémarrer l'application
pm2 restart dataautomation

# Vérifier les logs
pm2 logs dataautomation --lines 100
```

### Problème de permissions

```bash
# Ajuster les permissions
chmod -R 755 /root/dataAutomation
chmod -R 777 /root/dataAutomation/media
chmod +x /root/dataAutomation/start_prod.sh
```

## 💾 Sauvegarde

### Sauvegarder la base de données

```bash
# Sur le VPS
cd /root/dataAutomation
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)

# Télécharger la sauvegarde
scp root@38.242.254.203:/root/dataAutomation/db.sqlite3 ./backup/
```

### Sauvegarder les fichiers media

```bash
# Sur le VPS
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz media/

# Télécharger la sauvegarde
scp root@38.242.254.203:/root/dataAutomation/media_backup_*.tar.gz ./backup/
```

## 🔒 Sécurité

- ✅ DEBUG = False en production
- ✅ Firewall configuré (ports 22 et 8000 uniquement)
- ✅ CSRF_TRUSTED_ORIGINS configuré
- ⚠️ Changez le SECRET_KEY avant le déploiement
- ⚠️ Configurez HTTPS avec un certificat SSL si possible

## 📝 Notes

- Le serveur écoute sur le port 8000
- Gunicorn utilise 3 workers
- Timeout de 300 secondes (5 minutes) pour les longues exécutions
- Redémarrage automatique en cas de crash
- Les fichiers statiques sont dans `staticfiles/`
- Les fichiers media sont dans `media/`
