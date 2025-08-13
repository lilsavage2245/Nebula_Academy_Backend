# news/models/comment.py
from django.db import models
from django.conf import settings

class NewsComment(models.Model):
    post = models.ForeignKey(
        'news.NewsPost',
        on_delete=models.CASCADE,
        related_name='comments'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='news_comments'
    )

    content = models.TextField()

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    is_approved = models.BooleanField(default=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_news_comments'
    )

    approved_on = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        status = "Deleted" if self.is_deleted else "Active"
        return f"[{status}] Comment by {self.user.email} on {self.post.title}"

    @property
    def nesting_depth(self):
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth

    def is_reply(self):
        return self.parent is not None
