# application/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, F
from django.core.exceptions import ValidationError

class ApplicationType(models.TextChoices):
    PROGRAM = "PROGRAM", "Program"
    MODULE  = "MODULE",  "Module"

class ApplicationStatus(models.TextChoices):
    DRAFT        = "DRAFT",        "Draft"
    SUBMITTED    = "SUBMITTED",    "Submitted"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    ACCEPTED     = "ACCEPTED",     "Accepted"
    REJECTED     = "REJECTED",     "Rejected"
    WITHDRAWN    = "WITHDRAWN",    "Withdrawn"

class Application(models.Model):
    # Who applies
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    # what kind
    type = models.CharField(max_length=8, choices=ApplicationType.choices)

    # Targets (only one path is used depending on `type`)
    program = models.ForeignKey(
        "program.Program",
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="applications",
        help_text="For PROGRAM applications."
    )

    level = models.ForeignKey(
        "program.ProgramLevel",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="applications",
        help_text="Optional level (must belong to the selected Program)."
    )

    module = models.ForeignKey(
        "module.Module",
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="applications",
        help_text="For MODULE applications."
    )

    # workflow
    status = models.CharField(
        max_length=16,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT
    )
    applicant_note = models.TextField(blank=True)
    supporting_documents = models.FileField(
        upload_to='applications/docs/',
        blank=True, null=True
    )

    # scoring and audit
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='applications_reviewed'
    )
    review_comment = models.TextField(blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reviewed_on = models.DateTimeField(null=True, blank=True)

    submitted_on = models.DateTimeField(null=True, blank=True)

    # Free-form answers / attribution (optional)
    answers = models.JSONField(default=dict, blank=True, help_text="Structured answers snapshot")
    form_key = models.CharField(max_length=64, blank=True, help_text="Form/config identifier used")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # uniqueness: one active app per target per user
    class Meta:
        ordering = ["-submitted_on", "-created_at"]
        constraints = [
            # PROGRAM: require program, forbid module; level is optional
            models.CheckConstraint(
                name="app_program_requires_program_no_module",
                check=Q(type="PROGRAM", program__isnull=False, module__isnull=True) | ~Q(type="PROGRAM"),
            ),
            # MODULE: require module, forbid program/level
            models.CheckConstraint(
                name="app_module_requires_module_no_program",
                check=Q(type="MODULE", module__isnull=False, program__isnull=True, level__isnull=True) | ~Q(type="MODULE"),
            ),
            
        ]
    def clean(self):
        # If both program and level are provided, ensure the level belongs to the program
        if self.program_id and self.level_id:
            if self.level.program_id != self.program_id:
                raise ValidationError({"level": "Selected level does not belong to the chosen program."})

        # Optional: if PROGRAM application is SUBMITTED or beyond, require a target
        if self.type == ApplicationType.PROGRAM and self.status in {
            ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW, ApplicationStatus.ACCEPTED
        }:
            if not (self.program_id or self.level_id):
                raise ValidationError("PROGRAM applications must specify a program or level when submitted.")

        # Optional: forbid BOTH program and level empty when type=PROGRAM (even in DRAFT)
        # if self.type == ApplicationType.PROGRAM and not (self.program_id or self.level_id):
        #     raise ValidationError("PROGRAM applications must specify a program or level.")

    # ---- helpers ----
    def submit(self):
        if self.status == ApplicationStatus.DRAFT:
            self.status = ApplicationStatus.SUBMITTED
            self.submitted_on = timezone.now()
            self.save(update_fields=["status", "submitted_on"])

    def set_status(self, new_status: str, actor=None, note: str = ""):
        old = self.status
        if new_status == old:
            return
        self.status = new_status
        if new_status in (ApplicationStatus.UNDER_REVIEW, ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED):
            self.reviewed_on = timezone.now()
        self.save(update_fields=["status", "reviewed_on", "updated_at"])
        ApplicationEvent.log(self, actor, "STATUS_CHANGED", {"from": old, "to": new_status, "note": note})

    def __str__(self):
        if self.type == ApplicationType.PROGRAM:
            t = f"{self.program} (L{self.level.level_number})" if self.level_id else f"{self.program}"
        else:
            t = f"{self.module}"
        return f"{self.applicant.email} → {self.type}: {t} [{self.status}]"


class ApplicationEvent(models.Model):
    """Timeline/audit log."""
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=64)  # e.g., SUBMITTED, STATUS_CHANGED, NOTE_ADDED
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["application", "created_at"])]

    def __str__(self):
        return f"{self.action} by {self.actor_id or 'system'} at {self.created_at:%Y-%m-%d %H:%M}"

    @classmethod
    def log(cls, application: Application, actor, action: str, payload: dict | None = None):
        return cls.objects.create(application=application, actor=actor, action=action, payload=payload or {})


class ApplicationReview(models.Model):
    """Per-reviewer evaluation (optional rubric)."""
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="application_reviews")
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    rubric = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("application", "reviewer")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review by {self.reviewer_id} on {self.application_id} ({self.score or '-'})"