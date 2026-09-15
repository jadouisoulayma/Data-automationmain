"""
fifo.py — Rotation FIFO des fichiers workflow (inputs, backoffice, training, resultats).

Règle : conserver seulement les MAX_ITEMS derniers fichiers/dossiers dans chaque
répertoire surveille. Le plus ancien est supprimé automatiquement dès que la limite
est dépassée.

Appelé :
  - Au démarrage du serveur (ScriptsConfig.ready via apps.py)
  - Après chaque run pipeline (succès OU erreur) dans views.py
"""

import os
import shutil
import logging

logger = logging.getLogger(__name__)

MAX_ITEMS = 4  # nombre maximum de fichiers/dossiers à conserver par répertoire


def _workflow_root():
    """Retourne le chemin absolu de media/workflow/."""
    from django.conf import settings
    return os.path.join(settings.MEDIA_ROOT, "workflow")


def fifo_dossier_fichiers(dossier, max_items=MAX_ITEMS):
    """
    Garde seulement les `max_items` fichiers les plus récents dans `dossier`.
    Supprime les plus anciens (tri par date de modification).
    """
    if not os.path.isdir(dossier):
        return
    fichiers = sorted(
        [f for f in os.listdir(dossier) if os.path.isfile(os.path.join(dossier, f))],
        key=lambda f: os.path.getmtime(os.path.join(dossier, f))
    )
    for ancien in fichiers[:-max_items] if len(fichiers) > max_items else []:
        chemin = os.path.join(dossier, ancien)
        try:
            os.remove(chemin)
            logger.info("FIFO [%s]: supprimé fichier '%s'", os.path.basename(dossier), ancien)
        except Exception as e:
            logger.warning("FIFO [%s]: impossible de supprimer '%s' : %s", os.path.basename(dossier), ancien, e)


def fifo_dossier_sous_dossiers(dossier, max_items=MAX_ITEMS):
    """
    Garde seulement les `max_items` sous-dossiers les plus récents dans `dossier`.
    Supprime les plus anciens (tri alphabétique = tri par date grâce au nommage YYYYMMDD_HHMMSS).
    """
    if not os.path.isdir(dossier):
        return
    sous_dossiers = sorted(
        [d for d in os.listdir(dossier) if os.path.isdir(os.path.join(dossier, d))]
    )
    for ancien in sous_dossiers[:-max_items] if len(sous_dossiers) > max_items else []:
        chemin = os.path.join(dossier, ancien)
        try:
            shutil.rmtree(chemin)
            logger.info("FIFO [resultats]: supprimé dossier '%s'", ancien)
        except Exception as e:
            logger.warning("FIFO [resultats]: impossible de supprimer '%s' : %s", ancien, e)


def appliquer_fifo():
    """
    Point d'entrée principal — applique la rotation FIFO sur tous les répertoires
    du workflow : inputs, backoffice et resultats.
    Applique aussi la rotation sur les workflows en base de données (4 derniers).
    Le dossier training n'est pas géré ici : le fichier d'entraînement est fixe
    côté backend (script data/entarinementdataset.csv) et n'est pas uploadé par
    l'utilisateur.
    Sûr à appeler plusieurs fois (idempotent).
    """
    wf_root = _workflow_root()

    # Fichiers uploadés par l'utilisateur
    fifo_dossier_fichiers(os.path.join(wf_root, "inputs"))
    fifo_dossier_fichiers(os.path.join(wf_root, "backoffice"))

    # Sous-dossiers datés dans resultats/
    fifo_dossier_sous_dossiers(os.path.join(wf_root, "resultats"))

    # Workflows en base : garder les 4 derniers par utilisateur
    fifo_workflows_db(max_items=4)

    logger.info("FIFO: rotation appliquée (max %d par répertoire, max 4 workflows/user)", MAX_ITEMS)


def fifo_workflows_db(max_items=4):
    """
    Supprime les workflows les plus anciens en base de données (et leurs fichiers
    sur disque) pour chaque utilisateur, en ne gardant que les `max_items` derniers.
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        for user in User.objects.all():
            wfs = list(
                __import__("scripts.models", fromlist=["ProductWorkflow"])
                .ProductWorkflow.objects.filter(user=user).order_by("created_at")
            )
            anciens = wfs[:-max_items] if len(wfs) > max_items else []
            for ancien in anciens:
                try:
                    ancien.delete()  # delete() overridé supprime aussi les fichiers disque
                    logger.info("FIFO DB: supprimé workflow #%s (user=%s)", ancien.pk, user.username)
                except Exception as e:
                    logger.warning("FIFO DB: impossible de supprimer workflow #%s : %s", ancien.pk, e)
    except Exception as e:
        logger.warning("FIFO DB: erreur générale : %s", e)
