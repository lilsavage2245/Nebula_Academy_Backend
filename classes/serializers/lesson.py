# classes/serializers/lesson.py

from rest_framework import serializers
from django.db.models import Avg
from classes.models import Lesson, LessonMaterial
from classes.models.enums import LessonAudience, MaterialAudience
from core.serializers import UserSerializer  # Adjust if you're using a different user display
from program.models import ProgramLevel, Session
from module.models import Module
from classes.serializers.fields import DisplayChoiceField, UserSafeField, TimeSinceField
from achievement.serializers.base import ChoiceDisplayField

# --- LessonMaterial Serializer ---
class LessonMaterialSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField(read_only=True)
    audience_display = serializers.CharField(source='get_audience_display', read_only=True)
    material_type_display = serializers.CharField(source='get_material_type_display', read_only=True)
    uploaded_by = UserSerializer(read_only=True)
    uploaded_by_id = serializers.PrimaryKeyRelatedField(
        source='uploaded_by',
        queryset=UserSerializer.Meta.model.objects.all(),
        write_only=True,
        required=False
    )
    time_since = TimeSinceField(source='created_at')

    class Meta:
        model = LessonMaterial
        fields = [
            'id', 'lesson', 'title', 'material_type', 'material_type_display',
            'file', 'url','version', 'audience', 'audience_display',
            'is_active', 'uploaded_by', 'uploaded_by_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'download_url', 'uploaded_by']
    
    def validate(self, attrs):
        file = attrs.get('file') or getattr(self.instance, 'file', None)
        url = attrs.get('url') or getattr(self.instance, 'url', '')
        if bool(file) == bool(url):  # both set or both empty
            raise serializers.ValidationError("Provide exactly one of 'file' or 'url'.")
        return attrs

    def get_download_url(self, obj):
        return obj.download_url


# --- Lesson Display Serializer (for detail/list views) ---
class LessonSerializer(serializers.ModelSerializer):
    # Foreign key titles for frontend
    program_level_title = serializers.CharField(source='program_level.title', read_only=True)
    module_title = serializers.CharField(source='module.title', read_only=True)
    session_title = serializers.CharField(source='session.title', read_only=True)

    # Choice fields display
    delivery_display = serializers.CharField(source='get_delivery_display', read_only=True)
    audience_display = serializers.CharField(source='get_audience_display', read_only=True)
    
    # Metrics and content
    materials = LessonMaterialSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'slug', 'description', 'date',
            'delivery', 'delivery_display',
            'audience', 'audience_display',
            'program_level', 'program_level_title',
            'module', 'module_title',
            'session', 'session_title',
            'is_published', 'duration_minutes',
            'video_embed_url', 'worksheet_link',
            'allow_comments', 'allow_ratings',
            'comments_count', 'average_rating',
            'created_at', 'materials'
        ]
        read_only_fields = ['slug', 'created_at', 'comments_count', 'average_rating']

    def get_average_rating(self, obj):
        return obj.ratings.aggregate(avg=Avg('score'))['avg'] or 0


# --- Lesson Create/Update Serializer ---
class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'title', 'description', 'date',
            'delivery', 'audience',
            'program_level', 'module', 'session',
            'is_published', 'duration_minutes',
            'video_embed_url', 'worksheet_link',
            'allow_comments', 'allow_ratings'
        ]

# --- Lesson Summary Serializer (used in other apps like worksheets) ---
class LessonSummarySerializer(serializers.ModelSerializer):
    program_level_title = serializers.CharField(source='program_level.title', read_only=True)
    module_title = serializers.CharField(source='module.title', read_only=True)
    session_title = serializers.CharField(source='session.title', read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'slug', 'date',
            'program_level', 'program_level_title',
            'module', 'module_title',
            'session', 'session_title',
            'is_published',
        ]
        read_only_fields = fields
