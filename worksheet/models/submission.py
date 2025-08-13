# worksheet/models/submission.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from .worksheet import Worksheet
from .base import SubmissionStatus
from .upload_paths import submission_upload_path
from django.core.validators import MinValueValidator, MaxValueValidator

class WorksheetSubmission(models.Model):
    worksheet = models.ForeignKey(
        Worksheet,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='worksheet_submissions'
    )

    submitted_file = models.FileField(upload_to=submission_upload_path, null=True, blank=True)
    written_response = models.TextField(blank=True)
    submitted_at = models.DateTimeField(default=timezone.now)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='worksheet_reviews',
        limit_choices_to={'role__in': ['LECTURER', 'VOLUNTEER', 'GUEST']}
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional score (e.g. out of 100)",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    feedback = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.SUBMITTED,
        help_text="Current status of the submission"
    )

    class Meta:
        unique_together = ('worksheet', 'user')
        ordering = ['-submitted_at']

    def mark_reviewed(self, reviewer, score=None, feedback=""):
        self.reviewed_by = reviewer
        self.score = score
        self.feedback = feedback
        self.reviewed_at = timezone.now()
        self.status = SubmissionStatus.REVIEWED
        self.save(update_fields=['reviewed_by', 'score', 'feedback', 'reviewed_at', 'status'])

    def mark_resubmitted(self):
        self.status = SubmissionStatus.RESUBMITTED
        self.submitted_at = timezone.now()
        self.save(update_fields=['status', 'submitted_at'])

    @property
    def is_reviewed(self):
        return self.status == SubmissionStatus.REVIEWED

    @property
    def title(self):
        return self.worksheet.title if self.worksheet else "Untitled Worksheet"

    @property
    def is_late(self):
        return self.worksheet.due_date and self.submitted_at > self.worksheet.due_date

    def __str__(self):
        return f"{self.user.email} - {self.worksheet.title}"
