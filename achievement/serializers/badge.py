# achievements/serializers/badge.py

from rest_framework import serializers
from achievement.models import Badge, AwardedBadge
from achievement.serializers.base import ChoiceDisplayField, TimestampedSerializerMixin
from core.serializers import UserSerializer
from common.serializers.fields import ContentTypeField  # optional
from achievement.models.base import AchievementType, BadgeRarity


class BadgeSerializer(TimestampedSerializerMixin, serializers.ModelSerializer):
    achievement_type = ChoiceDisplayField(choices=AchievementType.choices)
    rarity = ChoiceDisplayField(choices=BadgeRarity.choices)
    content_type = ContentTypeField(required=False)

    class Meta:
        model = Badge
        fields = [
            'id', 'name', 'slug', 'description', 'image',
            'achievement_type', 'achievement_type_display',
            'rarity', 'rarity_display',
            'is_hidden', 'display_order',
            'content_type', 'object_id',
            'criteria', 'xp_reward',
            'is_active', 'valid_from', 'valid_until',
            'created_at'
        ]
        read_only_fields = ['slug', 'created_at']


class BadgeCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        exclude = ['slug', 'created_at']


class AwardedBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    awarded_since = serializers.SerializerMethodField()

    class Meta:
        model = AwardedBadge
        fields = ['id', 'user', 'badge', 'awarded_at', 'awarded_since']
        read_only_fields = fields

    def get_awarded_since(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.awarded_at) + " ago" if obj.awarded_at else None


class AwardedBadgeCreateSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(source='user', queryset=AwardedBadge._meta.get_field('user').related_model.objects.all())
    badge_id = serializers.PrimaryKeyRelatedField(source='badge', queryset=Badge.objects.all())

    class Meta:
        model = AwardedBadge
        fields = ['user_id', 'badge_id']
