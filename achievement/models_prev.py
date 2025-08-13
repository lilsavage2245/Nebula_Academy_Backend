# achievement/models.py
from django.db import models
from django.conf import settings
from common.mixins import SlugModelMixin
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class AchievementType(models.TextChoices):
    MILESTONE = 'MILESTONE', 'Milestone'
    PARTICIPATION = 'PARTICIPATION', 'Participation'
    PERFORMANCE = 'PERFORMANCE', 'Performance'
    PROJECT = 'PROJECT', 'Project'
    EVENT = 'EVENT', 'Event/Campaign'
    COMMUNITY = 'COMMUNITY', 'Community Contribution'
    SPECIAL = 'SPECIAL', 'Special Recognition'


def badge_image_upload_path(instance, filename):
    return f"achievement/badges/{instance.slug}/{filename}"

class BadgeRarity(models.TextChoices):
    COMMON = 'COMMON', 'Common'
    RARE = 'RARE', 'Rare'
    LEGENDARY = 'LEGENDARY', 'Legendary'
    SECRET = 'SECRET', 'Secret'

class Badge(SlugModelMixin, models.Model):
    slug_source_field = 'name'
    slug_max_length = 100

    name        = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image       = models.ImageField(upload_to=badge_image_upload_path, null=True, blank=True)

    achievement_type = models.CharField(
        max_length=30,
        choices=AchievementType.choices,
        default=AchievementType.MILESTONE
    )

    rarity = models.CharField(
        max_length=20,
        choices=BadgeRarity.choices,
        default=BadgeRarity.COMMON,
    )
    is_hidden = models.BooleanField(default=False, help_text="If true, badge is not shown until earned.")

    # Flexible linking to Module, Event, Role, UserGroup, etc.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id    = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    display_order = models.PositiveIntegerField(default=0)


    criteria     = models.JSONField(default=dict, help_text='e.g., {"quizzes_passed": 3}')
    xp_reward    = models.PositiveIntegerField(default=0)
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    valid_from   = models.DateTimeField(null=True, blank=True, help_text='When this badge becomes valid')
    valid_until  = models.DateTimeField(null=True, blank=True, help_text='When this badge expires')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name



class XPEvent(models.Model):
    """
    Logs all XP-related activities (automatic or manual).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='xp_events'
    )
    action = models.CharField(max_length=100)
    xp = models.IntegerField(help_text="Can be positive or negative")
    badge = models.ForeignKey('Badge', null=True, blank=True, on_delete=models.SET_NULL)
    related_object = models.JSONField(
        default=dict,
        blank=True,
        help_text="E.g., {'class_id': 5, 'quiz_id': 2}"
    )

    class XPSourceType(models.TextChoices):
        SYSTEM = 'SYSTEM', 'System-Generated'
        MANUAL = 'MANUAL', 'Manually Assigned'
        ACTION = 'ACTION', 'User Action'

    source = models.CharField(
        max_length=20,
        choices=XPSourceType.choices,
        default=XPSourceType.SYSTEM
    )

    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        sign = '+' if self.xp >= 0 else ''
        return f"{self.user.email} {sign}{self.xp} XP — {self.action}"


class UserLevel(models.Model):
    """
    XP thresholds and level titles.
    """
    level = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=100)
    xp_required = models.PositiveIntegerField()
    icon = models.ImageField(upload_to="achievement/level_icons/", null=True, blank=True)

    class Meta:
        ordering = ['level']

    def __str__(self):
        return f"Level {self.level} — {self.title}"


class UserProfileAchievement(models.Model):
    """
    Profile-level summary of user's XP and level.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='achievement_profile'
    )
    total_xp = models.PositiveIntegerField(default=0)
    current_level = models.ForeignKey(
        UserLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    last_updated = models.DateTimeField(auto_now=True)

    def update_level(self):
        """
        Dynamically updates user's level based on XP.
        """
        levels = UserLevel.objects.order_by('-xp_required')
        for level in levels:
            if self.total_xp >= level.xp_required:
                self.current_level = level
                break
        else:
            self.current_level = None
        self.save(update_fields=['current_level'])
    
    @property
    def next_level_xp(self):
        if self.current_level:
            next_level = UserLevel.objects.filter(
                xp_required__gt=self.current_level.xp_required
            ).order_by('xp_required').first()
            return next_level.xp_required if next_level else None
        return None


    def __str__(self):
        return f"{self.user.email} — XP: {self.total_xp}, Level: {self.current_level.level if self.current_level else 0}"

class AwardedBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='awarded_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')  # Prevent duplicate badge awards
