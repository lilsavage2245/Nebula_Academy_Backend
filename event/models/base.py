# event/models/base.py
from django.db import models

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


class EventStatus(models.TextChoices):
    UPCOMING = 'UPCOMING', 'Upcoming'
    ONGOING = 'ONGOING', 'Ongoing'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'
