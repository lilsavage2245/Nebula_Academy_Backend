# module/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import (
    Module, ModuleLevelLink, ModuleLecturer,
    ModuleMaterial, EvaluationComponent,
)


# -------------------
# Inlines
# -------------------

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


class ModuleMaterialInline(admin.StackedInline):
    """
    Stacked for richer fields. Shows both file and external_url so admins can pick one.
    Model validation enforces the correct combination per MaterialType.
    """
    model = ModuleMaterial
    extra = 0
    fields = (
        'title', 'slug', 'description',
        'type', 'audience',
        'file', 'external_url',
        'version', 'is_active',
        ('content_type', 'file_size'),
        'created_at',
        'admin_open_link', 'admin_download_link',
    )
    readonly_fields = ('slug', 'created_at', 'content_type', 'file_size', 'admin_open_link', 'admin_download_link')
    verbose_name = "Module Material"
    verbose_name_plural = "Module Materials"

    def admin_open_link(self, obj):
        if not obj.pk:
            return "-"
        # Uses storage URL if available (may be signed depending on storage backend)
        if obj.file and hasattr(obj.file, "url"):
            return format_html('<a href="{}" target="_blank">Open</a>', obj.file.url)
        if obj.external_url:
            return format_html('<a href="{}" target="_blank">External</a>', obj.external_url)
        return "-"
    admin_open_link.short_description = "Open"

    def admin_download_link(self, obj):
        if not obj.pk:
            return "-"
        try:
            url = reverse("module:module-materials-download", kwargs={
                "module_pk": obj.module.slug,  # nested router kwarg name
                "slug": obj.slug,
            })
            return format_html('<a href="{}" target="_blank">Download</a>', url)
        except Exception:
            return "-"
    admin_download_link.short_description = "Download"


class EvaluationComponentInline(admin.TabularInline):
    model = EvaluationComponent
    extra = 0
    fields = ['type', 'title', 'weight']
    readonly_fields = ['created_at']
    verbose_name = "Evaluation"
    verbose_name_plural = "Evaluations"


# -------------------
# Admins
# -------------------

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_standalone', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'prerequisites']
    list_filter = ['is_standalone', 'is_active']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    ordering = ['title']

    inlines = [
        ModuleLevelLinkInline,
        ModuleLecturerInline,
        ModuleMaterialInline,
        EvaluationComponentInline,
    ]

    actions = ["deactivate_all_materials"]

    @admin.action(description="Deactivate ALL materials in selected modules")
    def deactivate_all_materials(self, request, queryset):
        total = 0
        for module in queryset:
            updated = module.materials.update(is_active=False)
            total += updated
        self.message_user(request, f"Deactivated {total} materials across {queryset.count()} module(s).")


@admin.register(ModuleLevelLink)
class ModuleLevelLinkAdmin(admin.ModelAdmin):
    list_display = ['module', 'level', 'order']
    list_filter = ['level__program']
    autocomplete_fields = ['module', 'level']
    ordering = ['level', 'order']
    search_fields = ['module__title', 'level__title']


@admin.register(ModuleLecturer)
class ModuleLecturerAdmin(admin.ModelAdmin):
    list_display = ['module', 'lecturer', 'role']
    search_fields = ['lecturer__first_name', 'lecturer__last_name', 'lecturer__email', 'module__title']
    autocomplete_fields = ['module', 'lecturer']


@admin.register(ModuleMaterial)
class ModuleMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'type', 'audience', 'version', 'is_active', 'created_at', 'open_link', 'download_link']
    list_filter = ['type', 'audience', 'is_active', 'module']
    search_fields = ['title', 'module__title', 'version', 'description']
    autocomplete_fields = ['module']
    readonly_fields = ['slug', 'created_at', 'content_type', 'file_size', 'admin_open_link', 'admin_download_link']
    fields = (
        'module', 'title', 'slug', 'description',
        'type', 'audience',
        'file', 'external_url',
        'version', 'is_active',
        ('content_type', 'file_size'),
        'created_at',
        'admin_open_link', 'admin_download_link',
    )
    ordering = ['-created_at']

    def open_link(self, obj):
        if obj.file and hasattr(obj.file, "url"):
            return format_html('<a href="{}" target="_blank">Open</a>', obj.file.url)
        if obj.external_url:
            return format_html('<a href="{}" target="_blank">External</a>', obj.external_url)
        return "-"
    open_link.short_description = "Open"

    def download_link(self, obj):
        try:
            url = reverse("module:module-materials-download", kwargs={
                "module_pk": obj.module.slug,  # nested router kwarg name from rest_framework_nested
                "slug": obj.slug,
            })
            return format_html('<a href="{}" target="_blank">Download</a>', url)
        except Exception:
            return "-"
    download_link.short_description = "Download"

    # Reuse the inline helpers for detail page too
    def admin_open_link(self, obj):  # for readonly_fields
        return self.open_link(obj)
    def admin_download_link(self, obj):
        return self.download_link(obj)


@admin.register(EvaluationComponent)
class EvaluationComponentAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'type', 'weight', 'created_at']
    search_fields = ['title', 'module__title']
    list_filter = ['type', 'module']
    autocomplete_fields = ['module']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['module', 'type', 'title']


