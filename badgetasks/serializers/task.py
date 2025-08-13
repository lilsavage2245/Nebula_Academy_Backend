from rest_framework import serializers
from badgetasks.models import WeeklyTaskAssignment


class WeeklyTaskAssignmentSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_type = serializers.CharField(source='task.task_type', read_only=True)
    required_hours = serializers.IntegerField(source='task.required_hours', read_only=True)
    progress = serializers.JSONField()
    status = serializers.CharField()
    updated_at = serializers.DateTimeField()

    class Meta:
        model = WeeklyTaskAssignment
        fields = [
            'id', 'task_title', 'task_type', 'required_hours',
            'progress', 'status', 'updated_at'
        ]
