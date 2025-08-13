# support/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from common.mixins import SlugModelMixin


class SupportAudience(models.TextChoices):
    GUEST = 'GUEST', 'Website Visitor / Applicant'
    ENROLLED = 'ENROLLED', 'Enrolled Student / Parent'
    FREE = 'FREE', 'Free User (Student)'
    VOLUNTEER = 'VOLUNTEER', 'Volunteer'
    PARTNER = 'PARTNER', 'Partner / Collaborator'
    OTHER = 'OTHER', 'Other'


class SupportChannel(models.TextChoices):
    CHAT = 'CHAT', 'Live Chat'
    EMAIL = 'EMAIL', 'Email'
    WHATSAPP = 'WHATSAPP', 'WhatsApp'
    CALL = 'CALL', 'Call Booking'
    TICKET = 'TICKET', 'Support Ticket'
    FORM = 'FORM', 'Feedback Form'
    VIDEO = 'VIDEO', 'Video Guide'
    ARTICLE = 'ARTICLE', 'Support Article'


class SupportCategory(SlugModelMixin, models.Model):
    slug_source_field = 'name'
    slug_max_length = 100

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Support Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class SupportTopic(SlugModelMixin, models.Model):
    slug_source_field = 'title'
    slug_max_length = 150

    category = models.ForeignKey(SupportCategory, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    audience = models.CharField(max_length=20, choices=SupportAudience.choices, default=SupportAudience.OTHER)
    channel = models.CharField(max_length=20, choices=SupportChannel.choices, default=SupportChannel.TICKET)
    content = models.TextField(blank=True)
    attachment = models.FileField(upload_to='support/topics/', null=True, blank=True)
    video_url = models.URLField(blank=True)
    external_link = models.URLField(blank=True, help_text="Optional link to external doc/article")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class SupportTicket(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='support_tickets'
    )
    email = models.EmailField(blank=True)
    topic = models.ForeignKey(SupportTopic, on_delete=models.SET_NULL, null=True, related_name='tickets')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[('OPEN', 'Open'), ('IN_PROGRESS', 'In Progress'), ('RESOLVED', 'Resolved'), ('CLOSED', 'Closed')],
        default='OPEN'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def is_resolved(self):
        return self.status in ['RESOLVED', 'CLOSED']

    def __str__(self):
        return f"{self.subject} ({self.status})"


class SupportResponse(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='support_responses'
    )
    message = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Private note for internal team only")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Response to {self.ticket.subject} ({'Internal' if self.is_internal else 'Public'})"


class PageFeedback(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='page_feedback'
    )
    page_url = models.URLField()
    was_helpful = models.BooleanField()
    feedback_text = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        status = "👍" if self.was_helpful else "👎"
        return f"{status} on {self.page_url}"


class SatisfactionSurveyResponse(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='satisfaction_surveys'
    )
    email = models.EmailField(blank=True)
    overall_experience = models.IntegerField(help_text="1–5 rating")
    staff_friendliness = models.IntegerField(null=True, blank=True)
    problem_resolution = models.IntegerField(null=True, blank=True)
    response_speed = models.IntegerField(null=True, blank=True)
    would_recommend = models.BooleanField(default=False)
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Survey by {self.user.email if self.user else self.email or 'Guest'}"


class SupportBooking(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='support_bookings'
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    audience = models.CharField(
        max_length=20, choices=SupportAudience.choices,
        default=SupportAudience.GUEST
    )
    reason = models.CharField(max_length=255)
    preferred_datetime = models.DateTimeField()
    notes = models.TextField(blank=True)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.reason} ({self.audience})"
