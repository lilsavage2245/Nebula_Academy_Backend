# achievement/models/base.py
from django.db import models


class AchievementType(models.TextChoices):
    MILESTONE = 'MILESTONE', 'Milestone'
    PARTICIPATION = 'PARTICIPATION', 'Participation'
    PERFORMANCE = 'PERFORMANCE', 'Performance'
    PROJECT = 'PROJECT', 'Project'
    EVENT = 'EVENT', 'Event/Campaign'
    COMMUNITY = 'COMMUNITY', 'Community Contribution'
    SPECIAL = 'SPECIAL', 'Special Recognition'


class BadgeRarity(models.TextChoices):
    COMMON = 'COMMON', 'Common'
    RARE = 'RARE', 'Rare'
    LEGENDARY = 'LEGENDARY', 'Legendary'
    SECRET = 'SECRET', 'Secret'


def badge_image_upload_path(instance, filename):
    return f"achievement/badges/{instance.slug}/{filename}"
