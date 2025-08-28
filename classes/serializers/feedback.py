# classes/serializers/feedback.py

from rest_framework import serializers
from django.utils.timesince import timesince
from classes.models import LessonComment, LessonRating
from core.serializers import UserSerializer  # Centralized reusable user display
from classes.serializers.fields import UserSafeField, TimeSinceField

class RecursiveField(serializers.Serializer):
    """Render nested replies recursively."""
    def to_representation(self, value):
        parent_serializer = self.parent.parent.__class__
        return parent_serializer(value, context=self.context).data

class LessonCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonComment
        fields = ['lesson', 'parent', 'content']  # user comes from request

    def validate(self, data):
        parent = data.get('parent')
        lesson = data.get('lesson')
        if parent and parent.lesson_id != lesson.id:
            raise serializers.ValidationError("Parent must belong to the same lesson.")
        return data

class LessonCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    replies = RecursiveField(many=True, read_only=True)

    class Meta:
        model = LessonComment
        fields = [
            'id', 'lesson', 'parent', 'user', 'user_name', 'user_email',
            'content', 'created_at', 'replies'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'replies']


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
