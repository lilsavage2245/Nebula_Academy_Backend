# news/models.py
from django.db import models
from django.conf import settings
from common.mixins import SlugModelMixin
from django.utils import timezone

class Status(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PUBLISHED = 'PUBLISHED', 'Published'
    PENDING = 'PENDING', 'Pending Approval'

class NewsCategory(SlugModelMixin, models.Model):
    slug_source_field = 'name'
    slug_max_length = 100

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True, help_text="Optional CSS icon class or emoji")


    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class NewsPost(SlugModelMixin, models.Model):
    slug_source_field = 'title'
    slug_max_length = 200

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='news_posts'
    )

    category = models.ForeignKey(
        'NewsCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts'
    )

    summary = models.CharField(
        max_length=300,
        blank=True,
        help_text="Optional short summary for previews and feeds."
    )

    content = models.TextField()

    image = models.ImageField(
        upload_to='news/images/',
        blank=True,
        null=True,
        help_text='Optional cover image'
    )

    tags = models.JSONField(
        blank=True,
        null=True,
        help_text='List of relevant keywords or tags'
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT
    )

    allow_comments = models.BooleanField(default=True)

    view_count = models.PositiveIntegerField(default=0)

    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=512, blank=True)

    # Smart publish control
    published_on = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_on', '-created_at']

    def save(self, *args, **kwargs):
        # Auto-set publish date
        if self.status == Status.PUBLISHED and not self.published_on:
            self.published_on = timezone.now()

        # Auto-fill SEO fields if not manually set
        if not self.meta_title:
            self.meta_title = self.title[:255]

        if not self.meta_description:
            stripped_content = self.content.replace('\n', ' ').strip()
            self.meta_description = stripped_content[:500] + '...' if len(stripped_content) > 500 else stripped_content

        super().save(*args, **kwargs)

    @property
    def is_visible(self):
        return self.status == Status.PUBLISHED and self.published_on and self.published_on <= timezone.now()

    def __str__(self):
        return self.title

class NewsComment(models.Model):
    post = models.ForeignKey(
        'NewsPost',
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

    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete to hide inappropriate or flagged comments without removing from DB."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        status = "Deleted" if self.is_deleted else "Active"
        return f"[{status}] Comment by {self.user.email} on {self.post.title}"

    @property
    def nesting_depth(self):
        """
        Returns how deeply nested this comment is.
        Use this to limit reply depth in frontend/API.
        """
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth

    def is_reply(self):
        return self.parent is not None


class NewsReaction(models.Model):
    class ReactionType(models.TextChoices):
        LIKE = 'LIKE', '👍 Like'
        DISLIKE = 'DISLIKE', '👎 Dislike'
        # Optionally add more later:
        # LOVE = 'LOVE', '❤️ Love'
        # LAUGH = 'LAUGH', '😂 Laugh'
        # WOW = 'WOW', '😮 Wow'

    post = models.ForeignKey(
        'NewsPost',
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

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Optional IP address for analytics or abuse detection."
    )

    device_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Optional device fingerprint for reaction tracing."
    )

    reacted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')
        ordering = ['-reacted_at']

    def __str__(self):
        return f"{self.user.email} reacted {self.reaction} on '{self.post.title}'"

class NewsSubscriber(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='news_subscriptions'
    )

    # Optional: One of these can be null; but not both
    category = models.ForeignKey(
        'NewsCategory',
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
        help_text="Optional: how they subscribed (e.g., 'on_signup', 'article_view', etc.)"
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