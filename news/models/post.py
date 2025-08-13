# news/models/post.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from common.mixins import SlugModelMixin
from .base import Status

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
        'news.NewsCategory',
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

    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=512, blank=True)

    published_on = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_on', '-created_at']

    def save(self, *args, **kwargs):
        if self.status == Status.PUBLISHED and not self.published_on:
            self.published_on = timezone.now()

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
