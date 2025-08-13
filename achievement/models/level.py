# achievement/models/level.py

from django.db import models


class UserLevel(models.Model):
    level = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=100)
    xp_required = models.PositiveIntegerField()
    icon = models.ImageField(upload_to="achievement/level_icons/", null=True, blank=True)

    class Meta:
        ordering = ['level']

    def __str__(self):
        return f"Level {self.level} — {self.title}"
