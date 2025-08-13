# worksheet/models.py
from django.db import models
from django.conf import settings
from common.mixins import SlugModelMixin
from django.utils import timezone


class WorksheetAudience(models.TextChoices):
    ENROLLED = 'ENROLLED', 'Enrolled Students Only'
    FREE = 'FREE', 'Free Users'
    BOTH = 'BOTH', 'Both Enrolled and Free Users'

class SubmissionStatus(models.TextChoices):
    SUBMITTED = 'SUBMITTED', 'Submitted'
    REVIEWED = 'REVIEWED', 'Reviewed'
    RESUBMITTED = 'RESUBMITTED', 'Resubmitted'


def worksheet_file_upload_path(instance, filename):
    return f"worksheet/{instance.class_session.id}/{filename}"


class Worksheet(SlugModelMixin, models.Model):
    slug_source_field = 'title'
    slug_max_length = 50

    """
    Worksheet uploaded for a specific class/session.
    Can be used by free or enrolled users depending on audience.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True, blank=True)

    
    lesson = models.ForeignKey(
        'classes.Lesson',
        on_delete=models.CASCADE,
        related_name='worksheet'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_worksheet',
        limit_choices_to={'role__in': ['LECTURER', 'VOLUNTEER', 'GUEST']}
    )

    file = models.FileField(upload_to=worksheet_file_upload_path, blank=True, null=True)
    external_url = models.URLField(blank=True, help_text="If hosted externally (optional)")

    instructions = models.TextField(blank=True)

    audience = models.CharField(
        max_length=10,
        choices=WorksheetAudience.choices,
        default=WorksheetAudience.BOTH,
        help_text="Who can view/submit this worksheet"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def total_submissions(self):
        return self.submissions.count()

    def __str__(self):
        return f"{self.title} ({self.class_session.title})"


def submission_upload_path(instance, filename):
    return f"worksheet/submissions/{instance.worksheet.id}/{instance.user.id}/{filename}"


class WorksheetSubmission(models.Model):
    """
    A user's submission for a worksheet.
    """
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

    submitted_file = models.FileField(
        upload_to=submission_upload_path,
        null=True,
        blank=True
    )
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
        validators=[models.MinValueValidator(0), models.MaxValueValidator(100)]
    )
    feedback = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.SUBMITTED,
        help_text="Current status of the submission"
    )

    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('worksheet', 'user')
        ordering = ['-submitted_at']

    def mark_reviewed(self, reviewer, score=None, feedback=""):
        self.reviewed_by = reviewer
        self.score = score
        self.feedback = feedback
        self.reviewed_at = timezone.now()
        self.status = SubmissionStatus.REVIEWED
        self.save(update_fields=['reviewed_by', 'score', 'feedback', 'reviewed_at', 'reviewed'])
    
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


class WorksheetFormat(models.TextChoices):
    FILE = 'FILE', 'File Upload'
    LINK = 'LINK', 'External Link'
    INTERACTIVE = 'INTERACTIVE', 'Interactive Form'

format = models.CharField(
    max_length=15,
    choices=WorksheetFormat.choices,
    default=WorksheetFormat.FILE
)
