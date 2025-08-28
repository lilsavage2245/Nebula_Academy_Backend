# event/models/registration.py
from django.db import models
from django.conf import settings
from django.db.models import Q

class EventRegistration(models.Model):
    class RegistrationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        NON_BINARY = "NON_BINARY", "Non-binary"
        TRANSGENDER = "TRANSGENDER", "Transgender"
        INTERSEX = "INTERSEX", "Intersex"
        PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer not to say"
        OTHER = "OTHER", "Other"

    class Affiliation(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        PARENT = "PARENT", "Parent / Guardian"
        SCHOOL = "SCHOOL", "School"
        COMPANY = "COMPANY", "Company / Employer"
        OTHER = "OTHER", "Other"

    class ReasonForAttending(models.TextChoices):
        LEARN = "LEARN", "To Learn New Skills"
        CAREER = "CAREER", "Career Exploration"
        NETWORK = "NETWORK", "Networking"
        SUPPORT = "SUPPORT", "Supporting Someone (Child/Friend)"
        OTHER = "OTHER", "Other"

    # --- Required links (kept exactly as you had) ---
    event = models.ForeignKey('event.Event', on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='event_registrations'
    )  # optional (external attendees won't have a user)

    # --- Attendee info ---
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name  = models.CharField(max_length=100, blank=True, null=True)
    email      = models.EmailField(blank=True, null=True)  # <- important
    phone_number = models.CharField(max_length=20, blank=True)

    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    gender_other = models.CharField(max_length=100, blank=True)

    age = models.PositiveIntegerField(null=True, blank=True)

    affiliation = models.CharField(max_length=20, choices=Affiliation.choices, blank=True)
    affiliation_other = models.CharField(max_length=150, blank=True)

    reason_for_attending = models.CharField(max_length=20, choices=ReasonForAttending.choices, blank=True)
    reason_other = models.CharField(max_length=150, blank=True)

    # --- Workflow & tracking ---
    status = models.CharField(max_length=20, choices=RegistrationStatus.choices, default=RegistrationStatus.PENDING)
    attended = models.BooleanField(default=False)

    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-registered_at']
        # Prevent duplicates for both platform users and externals
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'user'],
                condition=Q(user__isnull=False),
                name='uniq_event_user_registration'
            ),
            models.UniqueConstraint(
                fields=['event', 'email'],
                condition=Q(email__isnull=False),
                name='uniq_event_email_registration'
            ),
        ]
        indexes = [
            models.Index(fields=['event', 'registered_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        who = self.user.email if self.user else self.email
        return f"{who} → {self.event.title}"
