from django.contrib import admin
from .models import LessonVideo
@admin.register(LessonVideo)
class LessonVideoAdmin(admin.ModelAdmin):
    list_display = ("lesson", "provider", "provider_id", "status", "duration_seconds", "created_at")
    search_fields = ("provider_id", "lesson__title")
