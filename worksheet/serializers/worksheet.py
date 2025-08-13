# worksheet/serializers/worksheet.py

from rest_framework import serializers
from worksheet.models import Worksheet
from worksheet.serializers.base import TimestampedSerializerMixin, ChoiceDisplayField
from worksheet.models.base import WorksheetAudience, WorksheetFormat
from core.serializers import UserSerializer
from classes.serializers.lesson import LessonSerializer, LessonSummarySerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class WorksheetSerializer(TimestampedSerializerMixin, serializers.ModelSerializer):
    """
    Lightweight read serializer for students or public views.
    Shows summary lesson info and uploader name.
    """
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)

    audience = ChoiceDisplayField(choices=WorksheetAudience.choices)
    format = ChoiceDisplayField(choices=WorksheetFormat.choices)

    total_submissions = serializers.IntegerField(read_only=True)

    class Meta:
        model = Worksheet
        fields = [
            'id', 'title', 'slug', 'description', 'instructions',
            'lesson_title', 'uploaded_by_name',
            'file', 'external_url', 'audience', 'audience_display',
            'format', 'format_display', 'due_date', 'created_at',
            'is_active', 'total_submissions',
        ]
        read_only_fields = ['slug', 'created_at', 'total_submissions']

class WorksheetStaffSerializer(TimestampedSerializerMixin, serializers.ModelSerializer):
    """
    Full read serializer for internal use: includes lesson & uploader details.
    """
    lesson = LessonSummarySerializer(read_only=True)
    uploaded_by = UserSerializer(read_only=True)

    audience = ChoiceDisplayField(choices=WorksheetAudience.choices)
    format = ChoiceDisplayField(choices=WorksheetFormat.choices)

    total_submissions = serializers.IntegerField(read_only=True)

    class Meta:
        model = Worksheet
        fields = [
            'id', 'title', 'slug', 'description', 'instructions',
            'lesson', 'uploaded_by',
            'file', 'external_url', 'audience', 'audience_display',
            'format', 'format_display', 'due_date',
            'created_at', 'is_active', 'total_submissions',
        ]


class WorksheetCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Write serializer for creating/updating worksheets by authorized users.
    Handles lesson and uploader references.
    """
    lesson_id = serializers.PrimaryKeyRelatedField(
        source='lesson',
        queryset=Worksheet._meta.get_field('lesson').related_model.objects.all()
    )
    uploaded_by_id = serializers.PrimaryKeyRelatedField(
        source='uploaded_by',
        queryset=User.objects.filter(role__in=['LECTURER', 'VOLUNTEER', 'GUEST']),
        required=False
    )

    class Meta:
        model = Worksheet
        exclude = ['slug', 'created_at']

    def create(self, validated_data):
        # Ensure uploader is either set or assigned from request.user
        if not validated_data.get('uploaded_by') and self.context.get('request'):
            validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)
