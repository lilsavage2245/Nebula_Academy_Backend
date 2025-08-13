# classes/serializers/attendance.py

from rest_framework import serializers
from classes.models import LessonAttendance
from .base import TimestampedSerializerMixin, OwnedByUserMixin
from .fields import TimeSinceField


class LessonAttendanceSerializer(TimestampedSerializerMixin, OwnedByUserMixin, serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    time_since = TimeSinceField(source='timestamp')

    class Meta:
        model = LessonAttendance
        fields = [
            'id', 'lesson', 'lesson_title',
            'user', 'user_id',
            'attended_live', 'attended_replay', 'attended',
            'watched_percent', 'duration',
            'timestamp', 'time_since'
        ]
        read_only_fields = [
            'id', 'timestamp', 'time_since',
            'lesson_title', 'attended', 'attended_replay'
        ]


class LessonAttendanceSummarySerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.get_full_name', read_only=True)
    lesson = serializers.CharField(source='lesson.title', read_only=True)
    time_since = TimeSinceField(source='timestamp')

    class Meta:
        model = LessonAttendance
        fields = ['lesson', 'user', 'attended', 'attended_live', 'attended_replay', 'time_since']
