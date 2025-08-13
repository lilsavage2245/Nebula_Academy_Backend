# dashboard/serializers/free

from rest_framework import serializers

class BadgeSerializer(serializers.Serializer):
    title = serializers.CharField()
    icon = serializers.CharField()

class WeeklyTaskSerializer(serializers.Serializer):
    title = serializers.CharField()
    status = serializers.CharField()                 # 'pending' | 'in_progress' | 'completed'
    type = serializers.CharField()                   # e.g. 'TIME_SPENT'
    required_hours = serializers.IntegerField()      # 0 for non TIME_SPENT
    progress = serializers.JSONField()

class FreeDashboardOverviewSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    email = serializers.EmailField()
    location = serializers.CharField()
    joined_date = serializers.DateField()
    program_level = serializers.CharField()
    completed_lessons = serializers.IntegerField()
    modules_in_progress = serializers.IntegerField()
    total_learning_time = serializers.CharField()
    weekly_activity = serializers.DictField(child=serializers.IntegerField())
    badges_earned = BadgeSerializer(many=True)
    weekly_tasks = WeeklyTaskSerializer(many=True)
    theme_preference = serializers.CharField()
    content_filter = serializers.CharField()
    profile_picture = serializers.CharField(allow_null=True, required=False)


class FreeLessonStatsSerializer(serializers.Serializer):
    upcoming_lessons = serializers.IntegerField()
    past_lessons = serializers.IntegerField()
    attended_lessons = serializers.IntegerField()
    unattended_past_lessons = serializers.IntegerField()

class LessonAttendedSummarySerializer(serializers.Serializer):
    lesson_id = serializers.IntegerField()
    title = serializers.CharField()
    viewed_at = serializers.DateTimeField()

class ModuleWithLessonsSerializer(serializers.Serializer):
    module_id = serializers.IntegerField()
    title = serializers.CharField()
    slug = serializers.SlugField()
    lessons = LessonAttendedSummarySerializer(many=True)

class LessonDetailInModuleSerializer(serializers.Serializer):
    lesson_id = serializers.IntegerField()
    title = serializers.CharField()
    date = serializers.DateTimeField()
    delivery = serializers.CharField()
    delivery_display = serializers.CharField()
    viewed_at = serializers.DateTimeField()
    video_embed_url = serializers.URLField()
    worksheet_link = serializers.URLField()
    has_comment_access = serializers.BooleanField()
    has_rating_access = serializers.BooleanField()