# event/models/event.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from common.mixins import SlugModelMixin
from .category import EventCategory
from .base import EventType, EventTargetGroup, EventFormat, EventStatus
from .speaker import EventSpeaker

class Event(SlugModelMixin, models.Model):
    slug_source_field = 'title'
    slug_max_length = 200

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()

    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, related_name='events')
    event_type = models.CharField(max_length=15, choices=EventType.choices, default=EventType.OTHER)
    target_group = models.CharField(max_length=20, choices=EventTargetGroup.choices, default=EventTargetGroup.ALL)

    audience_description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional explanation of who this event is for, e.g., 'Parents of Pre-Academy students aged 10–13'."
    )

    format = models.CharField(max_length=10, choices=EventFormat.choices, default=EventFormat.ONLINE)
    status = models.CharField(max_length=15, choices=EventStatus.choices, default=EventStatus.UPCOMING)

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)

    event_link = models.URLField(blank=True)
    venue = models.CharField(max_length=255, blank=True)

    tags = models.JSONField(blank=True, null=True, help_text="List of tags for filtering and search")

    banner_image = models.ImageField(upload_to='events/banners/', null=True, blank=True)
    attached_file = models.FileField(upload_to='events/files/', null=True, blank=True)

    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    published_on = models.DateTimeField(null=True, blank=True)

    is_registration_required = models.BooleanField(default=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)

    organizers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='organized_events', blank=True)

    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=512, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_datetime']

    def save(self, *args, **kwargs):
        if self.is_published and not self.published_on:
            self.published_on = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_full(self):
        return self.capacity and self.registrations.count() >= self.capacity

    @property
    def computed_status(self):
        now = timezone.now()
        if self.start_datetime > now:
            return "Upcoming"
        if self.end_datetime and self.end_datetime < now:
            return "Completed"
        if self.start_datetime <= now <= (self.end_datetime or now):
            return "Ongoing"
        return "Unknown"

    @property
    def speakers_list(self):
        """
        Returns a combined list of both user and guest speakers for easy display.
        """
        speakers = []
        for es in self.event_speakers.select_related('user', 'guest'):
            if es.speaker_type == EventSpeaker.SpeakerType.USER and es.user:
                speakers.append(es.user.get_full_name() or es.user.username)
            elif es.speaker_type == EventSpeaker.SpeakerType.GUEST and es.guest:
                speakers.append(es.guest.name)
        return speakers
    
    def __str__(self):
        return self.title
