# event/models.py
from django.db import models
from django.conf import settings
from common.mixins import SlugModelMixin
from django.utils import timezone


class EventCategory(SlugModelMixin, models.Model):
    """
    Grouping categories like 'Campaigns', 'Tech Events', 'Parent Webinars'.
    """
    slug_source_field = 'name'
    slug_max_length = 100

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Event Categories'

    def __str__(self):
        return self.name


class EventType(models.TextChoices):
    WEBINAR = 'WEBINAR', 'Webinar'
    WORKSHOP = 'WORKSHOP', 'Workshop'
    CAMPAIGN = 'CAMPAIGN', 'Campaign'
    MEETUP = 'MEETUP', 'Meetup'
    OTHER = 'OTHER', 'Other'


class EventTargetGroup(models.TextChoices):
    PUBLIC = 'PUBLIC', 'Public'
    FREE = 'FREE', 'Free Users Only'
    ENROLLED = 'ENROLLED', 'Enrolled Students Only'
    ALL = 'ALL', 'All Users'


class EventFormat(models.TextChoices):
    ONLINE = 'ONLINE', 'Online'
    IN_PERSON = 'IN_PERSON', 'In Person'
    HYBRID = 'HYBRID', 'Hybrid'


class Event(SlugModelMixin, models.Model):
    slug_source_field = 'title'
    slug_max_length = 200

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()

    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='event'
    )
    event_type = models.CharField(
        max_length=15,
        choices=EventType.choices,
        default=EventType.OTHER
    )
    target_group = models.CharField(
        max_length=20,
        choices=EventTargetGroup.choices,
        default=EventTargetGroup.ALL
    )
    format = models.CharField(
        max_length=10,
        choices=EventFormat.choices,
        default=EventFormat.ONLINE
    )

    # Schedule
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)

    # Location / Online
    event_link = models.URLField(blank=True, help_text="Zoom, YouTube, Meet, etc.")
    venue = models.CharField(max_length=255, blank=True, help_text="Physical venue (if applicable)")

    # Content & Media
    banner_image = models.ImageField(upload_to='event/banners/', null=True, blank=True)
    attached_file = models.FileField(upload_to='event/files/', null=True, blank=True)

    # Publishing & Control
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    published_on = models.DateTimeField(null=True, blank=True)

    # Registration Controls
    is_registration_required = models.BooleanField(default=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)

    organizers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='organized_events',
        blank=True
    )

    # SEO
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

    def __str__(self):
        return self.title


class EventRegistration(models.Model):
    """
    Tracks RSVPs or participation of users in an event.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)
    feedback_submitted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.user.email} registered for {self.event.title}"
