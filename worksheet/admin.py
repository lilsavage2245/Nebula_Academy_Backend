# worksheet/admin.py

from django.contrib import admin
from worksheet.models import Worksheet, WorksheetSubmission
from worksheet.models.base import SubmissionStatus


class WorksheetSubmissionInline(admin.TabularInline):
    model = WorksheetSubmission
    extra = 0
    fields = ('user', 'status', 'score', 'submitted_at', 'reviewed_by')
    readonly_fields = ('submitted_at',)
    show_change_link = True


@admin.register(Worksheet)
class WorksheetAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'lesson', 'audience', 'format', 'uploaded_by', 'created_at', 'is_active',
    )
    list_filter = ('audience', 'format', 'is_active')
    search_fields = ('title', 'description', 'lesson__title')
    readonly_fields = ('created_at',)
    inlines = [WorksheetSubmissionInline]
    autocomplete_fields = ('lesson', 'uploaded_by')


@admin.register(WorksheetSubmission)
class WorksheetSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'worksheet', 'user', 'status', 'score', 'submitted_at', 'reviewed_by', 'reviewed_at',
    )
    list_filter = ('status', 'reviewed_by', 'worksheet', 'worksheet__lesson')
    search_fields = ('user__email', 'worksheet__title')
    autocomplete_fields = ('worksheet', 'user', 'reviewed_by')
    readonly_fields = ('submitted_at', 'reviewed_at')
