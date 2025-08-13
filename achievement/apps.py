# achievement/apps.py
from django.apps import AppConfig


class AchievementConfig(AppConfig):
    name = 'achievement'
    verbose_name = 'Achievements & Gamification'

    def ready(self):
        # Import signals to ensure evaluations and XP/badge awards are hooked
        try:
            import achievement.signals  # noqa: F401
        except ImportError as e:
            # Signals module not present or import error
            raise e
