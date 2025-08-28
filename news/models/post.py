# news/models/post.py
# news/models/post.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.html import mark_safe
from common.mixins import SlugModelMixin
from .base import Status

# 3rd-party
import markdown as md
import re

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

    # Store Markdown here
    content = models.TextField(help_text="Markdown content")

    # Cached rendered HTML (auto-filled on save)
    content_html = models.TextField(blank=True)

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

    # Publish control
    published_on = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_on', '-created_at']

    # ---------- Rendering ----------
    def _render_markdown(self) -> str:
        return md.markdown(
            self.content or "",
            extensions=[
                "extra",       # tables, lists, etc.
                "nl2br",       # keep \n as <br>
                "sane_lists",
                "smarty",      # typographic quotes/dashes
            ]
        )

    def _extract_meta_description(self) -> str:
        """
        Make a readable meta description from rendered HTML.
        Keeps existing behavior but strips tags for cleaner SEO.
        """
        html = self._render_markdown()
        text = re.sub(r"<[^>]+>", " ", html)  # strip tags
        text = " ".join(text.split()).strip()
        return (text[:500] + '...') if len(text) > 500 else text

    # ---------- Save ----------
    def save(self, *args, **kwargs):
        # Auto-set publish date
        if self.status == Status.PUBLISHED and not self.published_on:
            self.published_on = timezone.now()

        # SEO defaults
        if not self.meta_title:
            self.meta_title = (self.title or "")[:255]
        if not self.meta_description:
            # Prefer summary if present; otherwise derive from content
            self.meta_description = (self.summary or self._extract_meta_description())[:512]

        # Render & cache HTML
        self.content_html = self._render_markdown()

        super().save(*args, **kwargs)

    @property
    def is_visible(self):
        return (
            self.status == Status.PUBLISHED and
            self.published_on and
            self.published_on <= timezone.now()
        )

    @property
    def rendered_content(self):
        """Convenience for templates: safe, cached HTML."""
        return mark_safe(self.content_html)

    def __str__(self):
        return self.title
