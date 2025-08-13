# achievement/serializers/level.py

from rest_framework import serializers
from achievement.models import UserLevel
from achievement.serializers.base import TimestampedSerializerMixin


class UserLevelSerializer(TimestampedSerializerMixin, serializers.ModelSerializer):
    """
    Displays user level info such as level number, title, XP threshold, and optional icon.
    Used in dashboards, progression visualizations, and admin views.
    """

    class Meta:
        model = UserLevel
        fields = ['id', 'level', 'title', 'xp_required', 'icon', 'created_at']
        read_only_fields = fields
