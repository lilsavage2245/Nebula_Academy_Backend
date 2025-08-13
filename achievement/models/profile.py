# achievement/models/profile.py

from django.db import models
from django.conf import settings
from .level import UserLevel


class UserProfileAchievement(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='achievement_profile'
    )
    total_xp = models.PositiveIntegerField(default=0)
    current_level = models.ForeignKey(
        UserLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    last_updated = models.DateTimeField(auto_now=True)

    def update_level(self):
        levels = UserLevel.objects.order_by('-xp_required')
        for level in levels:
            if self.total_xp >= level.xp_required:
                self.current_level = level
                break
        else:
            self.current_level = None
        self.save(update_fields=['current_level'])

    @property
    def next_level_xp(self):
        if self.current_level:
            next_level = UserLevel.objects.filter(
                xp_required__gt=self.current_level.xp_required
            ).order_by('xp_required').first()
            return next_level.xp_required if next_level else None
        return None

    def __str__(self):
        return f"{self.user.email} — XP: {self.total_xp}, Level: {self.current_level.level if self.current_level else 0}"
