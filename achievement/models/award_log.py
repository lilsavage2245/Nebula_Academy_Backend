# achievement/models/award_log
from django.db import models
from django.conf import settings
from achievement.models.badge import Badge


class BadgeAwardLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=100, blank=True, help_text="E.g. 'system_check', 'admin_panel', 'worksheet_signal'")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-awarded_at']

    def __str__(self):
        badge_name = getattr(self.badge, 'name', 'unknown badge')
        user_email = getattr(self.user, 'email', 'unknown user')
        return f"{user_email} awarded {badge_name} via {self.source or 'unknown'}"
