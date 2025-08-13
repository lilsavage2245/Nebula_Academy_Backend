# achievement/models/xp.py

from django.db import models
from django.conf import settings
from django.utils import timezone


class XPEvent(models.Model):
    class XPSourceType(models.TextChoices):
        SYSTEM = 'SYSTEM', 'System-Generated'
        MANUAL = 'MANUAL', 'Manually Assigned'
        ACTION = 'ACTION', 'User Action'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='xp_events'
    )
    action = models.CharField(max_length=100)
    xp = models.IntegerField(help_text="Can be positive or negative")
    badge = models.ForeignKey('achievement.Badge', null=True, blank=True, on_delete=models.SET_NULL)
    related_object = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=20, choices=XPSourceType.choices, default=XPSourceType.SYSTEM)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        sign = '+' if self.xp >= 0 else ''
        return f"{self.user.email} {sign}{self.xp} XP — {self.action}"
