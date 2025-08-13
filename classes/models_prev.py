# class/models.py
from django.db import models
from django.conf import settings
from module.models import Module
from program.models import ProgramLevel, Session
from common.mixins import SlugModelMixin, SoftDeleteModelMixin


class LessonAudience(models.TextChoices):
    FREE = 'FREE', 'Free Users'
    ENROLLED = 'ENROLLED', 'Enrolled Students'
    BOTH = 'BOTH', 'Both Free and Enrolled Users'
    STAFF = 'STAFF', 'Academy Staff Only'


class Lesson(SlugModelMixin, SoftDeleteModelMixin, models.Model):
    """
    A single class/lesson within a module or program level.
    Can be live or recorded. Supports material links, video embeds, ratings, and comments.
    """   
    DELIVERY_TYPE = [
        ('LIVE', 'Live Session'),
        ('REC', 'Recorded Video'),
        ('HYBRID', 'Live + Recording'),
    ]

    AUDIENCE_CHOICES = LessonAudience.choices

    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()

    program_level = models.ForeignKey(
        ProgramLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons'
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons'
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons'
    )

    delivery = models.CharField(max_length=10, choices=DELIVERY_TYPE, default='REC')
    audience = models.CharField(
        max_length=10,
        choices=LessonAudience.choices,
        default=LessonAudience.BOTH,
        help_text='Who can access this lesson'
    )

    slug = models.SlugField(unique=True, blank=True)
    is_published = models.BooleanField(default=False)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    video_embed_url = models.URLField(blank=True, help_text="YouTube, Vimeo or other embed link")
    material_links = models.JSONField(blank=True, null=True, help_text='List of URLs to slides, PDFs, resources')
    worksheet_link = models.URLField(blank=True, help_text="Optional worksheet link")

    allow_comments = models.BooleanField(default=True)
    allow_ratings = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



class LessonComment(models.Model):
    """
    Comments posted by free or enrolled users on a lesson.
    """
    lesson = models.ForeignKey(
        'Lesson',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.email} on {self.lesson.title}"


class LessonRating(models.Model):
    """
    Star rating (1-5) given by users for a lesson session.
    """
    lesson = models.ForeignKey(
        'Lesson',
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_ratings'
    )
    score = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text='Rating from 1 (worst) to 5 (best)'
    )
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lesson', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.score}★ by {self.user.email} on {self.lesson.title}"


class LessonAttendance(models.Model):
    """
    Tracks which users attended a class session.
    """
    lesson = models.ForeignKey(
        'Lesson',
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_attendances'
    )
    attended = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lesson', 'user')
        ordering = ['-timestamp']

    def __str__(self):
        status = "Attended" if self.attended else "Missed"
        return f"{self.user.get_full_name()} - {status} {self.lesson.title}"


class LessonReply(models.Model):
    """
    Tracks user replies to comments.
    """
    parent_comment = models.ForeignKey(
        LessonComment,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_replies'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Reply by {self.user.email} to {self.parent_comment.user.email}"


class MaterialAudience(models.TextChoices):
    FREE = 'FREE', 'Free Users'
    ENROLLED = 'ENROLLED', 'Enrolled Students'
    STAFF = 'STAFF', 'Academy Staff Only'
    BOTH = 'BOTH', 'Both Free and Enrolled Users'

class LessonMaterial(models.Model):
    """
    Tracks individual material files or links associated with a lesson.
    Supports versioning, audience restriction, and types.
    """
    MATERIAL_TYPE_CHOICES = [
        ('PDF', 'PDF / Slides'),
        ('LINK', 'External Link'),
        ('VIDEO', 'Video Embed'),
        ('DOC', 'Document'),
        ('ZIP', 'Compressed Resources'),
    ]

    lesson = models.ForeignKey(
        'Lesson',
        on_delete=models.CASCADE,
        related_name='materials'
    )
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPE_CHOICES)
    url = models.URLField(help_text="Link to the material (PDF, video, resource)")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_lesson_materials'
    )
    version = models.PositiveIntegerField(default=1, help_text="Increment for newer versions")
    audience = models.CharField(
        max_length=10,
        choices=MaterialAudience.choices,
        default=MaterialAudience.BOTH
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('lesson', 'title', 'version')

    def __str__(self):
        return f"{self.lesson.title} - {self.title} v{self.version}"
