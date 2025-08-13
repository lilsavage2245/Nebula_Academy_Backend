# worksheet/serializers/submission.py

from rest_framework import serializers
from worksheet.models import WorksheetSubmission
from worksheet.models.base import SubmissionStatus
from worksheet.serializers.base import TimestampedSerializerMixin, ChoiceDisplayField
from core.serializers import UserSerializer
from worksheet.serializers.worksheet import WorksheetSerializer, WorksheetStaffSerializer


class WorksheetSubmissionSerializer(TimestampedSerializerMixin, serializers.ModelSerializer):
    """
    Public-facing read-only serializer for student submissions.
    """
    worksheet = WorksheetSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)

    status = ChoiceDisplayField(choices=SubmissionStatus.choices)
    is_late = serializers.BooleanField(read_only=True)
    title = serializers.CharField(source='worksheet.title', read_only=True)
    submitted_since = serializers.SerializerMethodField()

    class Meta:
        model = WorksheetSubmission
        fields = [
            'id', 'worksheet', 'user', 'title',
            'submitted_file', 'written_response',
            'submitted_at', 'submitted_since', 'is_late',
            'status', 'status_display',
            'score', 'feedback', 'reviewed_by', 'reviewed_at',
            'created_at'
        ]
        read_only_fields = fields

    def get_submitted_since(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.submitted_at) + " ago" if obj.submitted_at else None



class WorksheetSubmissionStaffSerializer(TimestampedSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for internal staff views — includes worksheet and review details.
    """
    worksheet = WorksheetStaffSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    
    status = ChoiceDisplayField(choices=SubmissionStatus.choices)
    is_late = serializers.BooleanField(read_only=True)

    class Meta:
        model = WorksheetSubmission
        fields = [
            'id', 'worksheet', 'user', 'submitted_file', 'written_response',
            'submitted_at', 'status', 'status_display', 'is_late',
            'score', 'feedback', 'reviewed_by', 'reviewed_at', 'created_at'
        ]


class WorksheetSubmissionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer used by students to submit a worksheet.
    """
    worksheet_id = serializers.PrimaryKeyRelatedField(
        source='worksheet',
        queryset=WorksheetSubmission._meta.get_field('worksheet').related_model.objects.all()
    )

    class Meta:
        model = WorksheetSubmission
        fields = [
            'worksheet_id', 'submitted_file', 'written_response'
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class WorksheetSubmissionReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for lecturers/staff to review and score a submission.
    """
    score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    feedback = serializers.CharField(required=False)

    class Meta:
        model = WorksheetSubmission
        fields = ['score', 'feedback']

    def update(self, instance, validated_data):
        reviewer = self.context['request'].user
        score = validated_data.get('score')
        feedback = validated_data.get('feedback', '')
        instance.mark_reviewed(reviewer=reviewer, score=score, feedback=feedback)
        return instance
