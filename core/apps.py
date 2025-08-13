from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.signals
        # Importing signals to ensure they are registered
        # This is necessary to ensure that the signal handlers are connected
        # when the application starts.
        # The import should be done here to avoid circular imports.
