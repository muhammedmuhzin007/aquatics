from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'
    
    def ready(self):
        # Import signals when app registry is ready so handlers can connect safely
        try:
            from . import signals  # noqa: F401
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Failed to import store.signals')

