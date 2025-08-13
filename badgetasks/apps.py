from django.apps import AppConfig

class BadgetasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'badgetasks'

    def ready(self):
        import badgetasks.signals
