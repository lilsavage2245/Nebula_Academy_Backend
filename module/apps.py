from django.apps import AppConfig


class ModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'module'

    def ready(self):
        # Import signals to ensure they are registered
        import module.signals