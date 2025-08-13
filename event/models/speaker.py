# event/models/speaker.py
from django.db import models
from django.conf import settings

class Speaker(models.Model):
    """
    Guest speakers not registered on the platform.
    """
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='speakers/', blank=True, null=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class EventSpeaker(models.Model):
    class SpeakerType(models.TextChoices):
        USER = 'USER', 'Platform User'
        GUEST = 'GUEST', 'Guest Speaker'

    event = models.ForeignKey(
        'event.Event', on_delete=models.CASCADE, related_name='event_speakers'
    )
    speaker_type = models.CharField(
        max_length=10, choices=SpeakerType.choices, default=SpeakerType.GUEST
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Used if the speaker is a platform user"
    )
    guest = models.ForeignKey(
        Speaker,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Used if the speaker is an external guest"
    )
    role = models.CharField(max_length=255, blank=True, help_text="e.g., Keynote, Panelist")
    speaker_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['speaker_order']
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'user', 'guest'], name='unique_event_speaker_entry'
            )
        ]

    def __str__(self):
        if self.speaker_type == self.SpeakerType.USER and self.user:
            return f"{self.user.get_full_name()} (User)"
        elif self.speaker_type == self.SpeakerType.GUEST and self.guest:
            return f"{self.guest.name} (Guest)"
        return f"Speaker for {self.event.title}"
