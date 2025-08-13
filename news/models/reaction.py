# news/models/reaction.py
from django.db import models
from django.conf import settings

class NewsReaction(models.Model):
    class ReactionType(models.TextChoices):
        LIKE = 'LIKE', '👍 Like'
        DISLIKE = 'DISLIKE', '👎 Dislike'

    post = models.ForeignKey(
        'news.NewsPost',
        on_delete=models.CASCADE,
        related_name='reactions'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='news_reactions'
    )

    reaction = models.CharField(
        max_length=10,
        choices=ReactionType.choices,
        default=ReactionType.LIKE
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_id = models.CharField(max_length=255, null=True, blank=True)
    reacted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')
        ordering = ['-reacted_at']

    def __str__(self):
        return f"{self.user.email} reacted {self.reaction} on '{self.post.title}'"
