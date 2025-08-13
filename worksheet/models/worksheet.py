# worksheet/models/worksheet.py
from django.db import models
from django.conf import settings
from common.mixins import SlugModelMixin
from .base import WorksheetAudience, WorksheetFormat
from .upload_paths import worksheet_file_upload_path

class Worksheet(SlugModelMixin, models.Model):
    slug_source_field = 'title'
    slug_max_length = 50

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True, blank=True)

    due_date = models.DateTimeField(null=True, blank=True)

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

    format = models.CharField(
        max_length=15,
        choices=WorksheetFormat.choices,
        default=WorksheetFormat.FILE
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def total_submissions(self):
        return self.submissions.count()

    def __str__(self):
        return f"{self.title} ({self.lesson.title})"
