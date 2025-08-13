# classes/serializers/feedback.py

from rest_framework import serializers
from django.utils.timesince import timesince
from classes.models import LessonComment, LessonReply, LessonRating
from core.serializers import UserSerializer  # Centralized reusable user display
from classes.serializers.fields import UserSafeField, TimeSinceField

# --- Lesson Reply Serializer ---
class LessonReplySerializer(serializers.ModelSerializer):
    user = UserSafeField()
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=UserSerializer.Meta.model.objects.all(),
        write_only=True
    )
    time_since = TimeSinceField(source='created_at')

    class Meta:
        model = LessonReply
        fields = ['id', 'parent_comment', 'user', 'user_id', 'content', 'created_at', 'time_since']
        read_only_fields = ['id', 'created_at']


# --- Lesson Comment Serializer ---
class LessonCommentSerializer(serializers.ModelSerializer):
    user = UserSafeField()
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=UserSerializer.Meta.model.objects.all(),
        write_only=True
    )
    replies = LessonReplySerializer(many=True, read_only=True)
    reply_count = serializers.SerializerMethodField()
    time_since = TimeSinceField(source='created_at')

    class Meta:
        model = LessonComment
        fields = [
            'id', 'lesson', 'user', 'user_id', 'content',
            'created_at', 'time_since', 'replies', 'reply_count'
        ]
        read_only_fields = ['id', 'created_at']

    def get_reply_count(self, obj):
        return obj.replies.count()


# --- Lesson Rating Serializer ---
class LessonRatingSerializer(serializers.ModelSerializer):
    user = UserSafeField()
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=UserSerializer.Meta.model.objects.all(),
        write_only=True
    )
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    time_since = TimeSinceField(source='created_at')

    class Meta:
        model = LessonRating
        fields = [
            'id', 'lesson', 'lesson_title',
            'score', 'review',
            'user', 'user_id', 'created_at', 'time_since'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_score(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Score must be between 1 and 5.")
        return value
