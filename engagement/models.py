# engagement/models.py

from django.db import models
from django.conf import settings

class EngagementPing(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="engagement_pings")
    # Round to minute to dedupe easily
    minute = models.DateTimeField(db_index=True, help_text="UTC minute representing activity interval")
    page = models.CharField(max_length=128, blank=True)  # optional: e.g. '/lessons/123'
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("user", "minute")   # ← critical: one ping per minute per user
        indexes = [models.Index(fields=["user", "minute"])]
        ordering = ["-minute"]

    def __str__(self):
        return f"{self.user.email} @ {self.minute.isoformat()}"
