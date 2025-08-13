# notification/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone


class NotificationType(models.TextChoices):
    SYSTEM = 'SYSTEM', 'System Message'
    EVENT = 'EVENT', 'Event Update'
    CLASS = 'CLASS', 'Class Reminder'
    ARTICLE = 'ARTICLE', 'New Article / Comment'
    SUPPORT = 'SUPPORT', 'Support Reply'
    CERTIFICATE = 'CERTIFICATE', 'Certificate Issued'
    REMINDER = 'REMINDER', 'Reminder'
    APPLICATION = 'APPLICATION', 'Application Update'
    PAYMENT = 'PAYMENT', 'Payment Notice'
    GENERAL = 'GENERAL', 'General Info'


class DeliveryMethod(models.TextChoices):
    IN_APP = 'IN_APP', 'In-App'
    EMAIL = 'EMAIL', 'Email'
    PUSH = 'PUSH', 'Push Notification'  # for future use


class Notification(models.Model):
    """
    A notification directed at a specific user.
    """
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    link = models.URLField(
        blank=True,
        help_text="Optional URL for redirection (e.g., class, article, dashboard item)"
    )

    delivery_method = models.CharField(
        max_length=10,
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.IN_APP
    )

    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def __str__(self):
        return f"To {self.recipient.email} — {self.title}"


class NotificationPreference(models.Model):
    """
    Optional user settings for how and when they receive notifications.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # Preferred delivery channels
    email = models.BooleanField(default=True)
    sms = models.BooleanField(default=False)  # for future integrations
    in_app = models.BooleanField(default=True)

    # Opt-in for specific notification types
    types = models.JSONField(
        default=list,
        help_text="List of NotificationType values the user wants to receive"
    )

    # Quiet hours (no notification delivery between these times)
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Silence period start (e.g., 22:00)"
    )
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text="Silence period end (e.g., 07:00)"
    )

    def __str__(self):
        return f"Notification preferences for {self.user.email}"
