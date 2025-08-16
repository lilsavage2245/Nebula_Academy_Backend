# application/apps.py
from django.apps import AppConfig

class ApplicationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "application"

    def ready(self):
        from . import signals  # noqa
