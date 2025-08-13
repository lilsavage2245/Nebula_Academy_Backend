# achievement/serializers/xp.py

from rest_framework import serializers
from achievement.models import XPEvent
from core.serializers import UserSerializer
from achievement.serializers.badge import BadgeSerializer
from achievement.serializers.base import TimestampedSerializerMixin, ChoiceDisplayField
from django.utils.timesince import timesince


class XPEventSerializer(TimestampedSerializerMixin, serializers.ModelSerializer):
    """
    Read-only serializer for XP activity log.
    Includes human-readable source label, time since, and related badge.
    """
    user = UserSerializer(read_only=True)
    badge = BadgeSerializer(read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    time_since = serializers.SerializerMethodField()

    class Meta:
        model = XPEvent
        fields = [
            'id', 'user', 'action', 'xp',
            'badge', 'related_object',
            'source', 'source_display',
            'timestamp', 'time_since', 'created_at'
        ]
        read_only_fields = fields

    def get_time_since(self, obj):
        return timesince(obj.timestamp) + " ago" if obj.timestamp else None


class XPEventCreateSerializer(serializers.ModelSerializer):
    """
    Used by staff to manually award or adjust XP.
    """
    class Meta:
        model = XPEvent
        fields = ['user', 'action', 'xp', 'badge', 'related_object', 'source']
