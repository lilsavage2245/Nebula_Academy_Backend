from django.contrib import admin
from .models import (
    Module, ModuleLevelLink, ModuleLecturer,
    LectureMaterial, EvaluationComponent
)
from achievement.models import Badge

# --- Inlines ---

class ModuleLevelLinkInline(admin.TabularInline):
    model = ModuleLevelLink
    extra = 0
    autocomplete_fields = ['level']
    ordering = ['order']
    verbose_name = "Linked Level"
    verbose_name_plural = "Linked Levels"


class ModuleLecturerInline(admin.TabularInline):
    model = ModuleLecturer
    extra = 0
    autocomplete_fields = ['lecturer']
    verbose_name = "Lecturer"
    verbose_name_plural = "Lecturers"


class LectureMaterialInline(admin.StackedInline):  # Stacked for richer fields
    model = LectureMaterial
    extra = 0
    fields = ['title', 'audience', 'slides', 'video_url']
    readonly_fields = ['created_at']
    verbose_name = "Lecture Material"
    verbose_name_plural = "Lecture Materials"


class EvaluationComponentInline(admin.TabularInline):  # Tabular is fine for short fields
    model = EvaluationComponent
    extra = 0
    fields = ['type', 'title', 'weight']
    readonly_fields = ['created_at']
    verbose_name = "Evaluation"
    verbose_name_plural = "Evaluations"

# --- Main Admin ---

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_standalone', 'created_at']
    search_fields = ['title', 'description']
    list_filter = ['is_standalone']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [
        ModuleLevelLinkInline,
        ModuleLecturerInline,
        LectureMaterialInline,
        EvaluationComponentInline
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['title']
    #filter_horizontal = ['levels']  # Power UX for M2M


# @admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'linked_to', 'achievement_type', 'xp_reward', 'is_active', 'created_at', 'has_image']
    list_filter = ['achievement_type', 'is_active', 'content_type']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = "Image Uploaded"

    def linked_to(self, obj):
        """Human-readable link target (e.g., 'Module: Web Dev')"""
        if obj.content_object:
            return f"{obj.content_type.model.capitalize()}: {str(obj.content_object)}"
        return "-"
    linked_to.short_description = "Linked To"


@admin.register(ModuleLevelLink)
class ModuleLevelLinkAdmin(admin.ModelAdmin):
    list_display = ['module', 'level', 'order']
    list_filter = ['level__program']
    autocomplete_fields = ['module', 'level']
    ordering = ['level', 'order']


@admin.register(ModuleLecturer)
class ModuleLecturerAdmin(admin.ModelAdmin):
    list_display = ['module', 'lecturer', 'role']
    search_fields = ['lecturer__first_name', 'lecturer__last_name']
    autocomplete_fields = ['module', 'lecturer']


@admin.register(LectureMaterial)
class LectureMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'audience', 'created_at']
    search_fields = ['title', 'module__title']
    autocomplete_fields = ['module']
    readonly_fields = ['created_at']


@admin.register(EvaluationComponent)
class EvaluationComponentAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'type', 'weight', 'created_at']
    search_fields = ['title', 'module__title']
    list_filter = ['type']
    autocomplete_fields = ['module']
    readonly_fields = ['created_at', 'updated_at']
