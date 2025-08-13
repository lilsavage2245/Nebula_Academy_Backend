from django.contrib import admin
from badgetasks.models import WeeklyTask, WeeklyTaskAssignment


@admin.register(WeeklyTask)
class WeeklyTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task_type', 'is_active', 'created_at')
    list_filter = ('task_type', 'is_active')


@admin.register(WeeklyTaskAssignment)
class WeeklyTaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'status', 'updated_at')
    list_filter = ('status', 'task__task_type')
    search_fields = ('user__email', 'task__title')
    readonly_fields = ('assigned_at', 'updated_at')
    list_editable = ('status',)

# Register your models here.
