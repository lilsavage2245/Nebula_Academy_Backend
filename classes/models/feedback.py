# classes/serializers/feedback.py
from django.db import models
from django.conf import settings
from .lesson import Lesson


class LessonComment(models.Model):
    """
    Tree-structured comments on a lesson (comments & replies in one table).
    Use `parent` to reply to any comment; unlimited nesting.
    """
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']  # chronological within a thread
        indexes = [
            models.Index(fields=['lesson', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.user.email} on {self.lesson.title}"

    @property
    def is_root(self):
        return self.parent_id is None

    def clean(self):
        # Ensure parent belongs to same lesson
        if self.parent and self.parent.lesson_id != self.lesson_id:
            from django.core.exceptions import ValidationError
            raise ValidationError("Parent comment must belong to the same lesson.")

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
