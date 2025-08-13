# classes/models/lesson.py
from django.db import models
from django.conf import settings
from common.mixins import SlugModelMixin
from .base import SoftDeleteModelMixin
from .enums import LessonAudience, MaterialAudience
from module.models import Module
from program.models import ProgramLevel, Session


class Lesson(SlugModelMixin, SoftDeleteModelMixin, models.Model):
    DELIVERY_TYPE = [
        ('LIVE', 'Live Session'),
        ('REC', 'Recorded Video'),
        ('HYBRID', 'Live + Recording'),
    ]

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons_created'
    )


    AUDIENCE_CHOICES = LessonAudience.choices

    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()

    program_level = models.ForeignKey(ProgramLevel, on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons')
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons')
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons')

    delivery = models.CharField(max_length=10, choices=DELIVERY_TYPE, default='REC')
    audience = models.CharField(max_length=10, choices=LessonAudience.choices, default=LessonAudience.BOTH)

    is_active = models.BooleanField(default=True)

    slug = models.SlugField(unique=True, blank=True)
    is_published = models.BooleanField(default=False)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    video_embed_url = models.URLField(blank=True)
    worksheet_link = models.URLField(blank=True)

    allow_comments = models.BooleanField(default=True)
    allow_ratings = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class LessonMaterial(models.Model):
    MATERIAL_TYPE_CHOICES = [
        ('PDF', 'PDF / Slides'),
        ('LINK', 'External Link'),
        ('VIDEO', 'Video Embed'),
        ('DOC', 'Document'),
        ('ZIP', 'Compressed Resources'),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPE_CHOICES)
    url = models.URLField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_lesson_materials')
    version = models.PositiveIntegerField(default=1)
    audience = models.CharField(max_length=10, choices=MaterialAudience.choices, default=MaterialAudience.BOTH)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('lesson', 'title', 'version')

    def __str__(self):
        return f"{self.lesson.title} - {self.title} v{self.version}"
