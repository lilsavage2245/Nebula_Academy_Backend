# achievement/models/badge.py

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from common.mixins import SlugModelMixin
from achievement.models.base import AchievementType, BadgeRarity, badge_image_upload_path
from module.models import Module


class Badge(SlugModelMixin, models.Model):
    slug_source_field = 'name'
    slug_max_length = 100

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=badge_image_upload_path, null=True, blank=True)

    achievement_type = models.CharField(
        max_length=50,
        choices=AchievementType.choices,
        default=AchievementType.MILESTONE
    )
    rarity = models.CharField(
        max_length=20,
        choices=BadgeRarity.choices,
        default=BadgeRarity.COMMON,
    )

    module = models.ForeignKey(
        Module,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='badges',
        help_text="Optional. Badge is specific to a module"
    )
    is_hidden = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    criteria = models.JSONField(default=dict)
    xp_reward = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AwardedBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='awarded_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')
