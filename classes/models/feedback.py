# classes/serializers/feedback.py
from django.db import models
from django.conf import settings
from .lesson import Lesson


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
