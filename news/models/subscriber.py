# news/models/subscriber.py
from django.db import models
from django.conf import settings

class NewsSubscriber(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='news_subscriptions'
    )

    category = models.ForeignKey(
        'news.NewsCategory',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subscribers'
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subscribed_followers'
    )

    subscribed_at = models.DateTimeField(auto_now_add=True)

    source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional: how they subscribed (e.g., 'on_signup', 'article_view')"
    )

    class Meta:
        unique_together = (
            ('user', 'category'),
            ('user', 'author'),
        )
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(category__isnull=False) |
                    models.Q(author__isnull=False)
                ),
                name="at_least_one_subscription_target"
            )
        ]
        ordering = ['-subscribed_at']

    def __str__(self):
        if self.category:
            return f"{self.user.email} subscribed to category '{self.category.name}'"
        elif self.author:
            return f"{self.user.email} subscribed to author '{self.author.get_full_name()}'"
        return f"{self.user.email} subscription"

    @property
    def is_category_subscription(self):
        return self.category is not None

    @property
    def is_author_subscription(self):
        return self.author is not None
