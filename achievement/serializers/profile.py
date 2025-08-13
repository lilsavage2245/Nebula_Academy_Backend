# achievement/serializers/profile.py

from rest_framework import serializers
from achievement.models import UserProfileAchievement
from achievement.serializers.level import UserLevelSerializer
from core.serializers import UserSerializer
from achievement.serializers.base import TimestampedSerializerMixin


class UserProfileAchievementSerializer(TimestampedSerializerMixin, serializers.ModelSerializer):
    """
    Displays a user's XP stats and level progression.
    Intended for frontend dashboards, profiles, and gamification insights.
    """
    user = UserSerializer(read_only=True)
    current_level = UserLevelSerializer(read_only=True)
    next_level_xp = serializers.IntegerField(read_only=True)
    total_xp = serializers.IntegerField(read_only=True)
    last_updated = serializers.DateTimeField(read_only=True)

    class Meta:
        model = UserProfileAchievement
        fields = [
            'id', 'user', 'total_xp', 'current_level',
            'next_level_xp', 'last_updated', 'created_at'
        ]
        read_only_fields = fields

