from django.apps import AppConfig


class ScriptsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "scripts"

    def ready(self):
        """Appelé une seule fois au démarrage du serveur Django."""
        try:
            from .fifo import appliquer_fifo
            appliquer_fifo()
        except Exception as e:
            # Ne jamais bloquer le démarrage du serveur
            import logging
            logging.getLogger(__name__).warning("FIFO au démarrage échoué : %s", e)
