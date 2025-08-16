# program/admin.py
from django import forms
from django.contrib import admin
from .models import Program, ProgramLevel, Session, ProgramCategory


class ProgramAdminForm(forms.ModelForm):
    # Force a proper <select> with enum values (PRE/BEG/INT/ADV)
    category = forms.ChoiceField(choices=ProgramCategory.choices)

    class Meta:
        model = Program
        fields = "__all__"

class ProgramLevelInline(admin.TabularInline):
    model = ProgramLevel
    extra = 0
    fields = ('level_number', 'title', 'description')
    ordering = ('level_number',)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    form = ProgramAdminForm
    list_display = ('name', 'category', 'director', 'created_at')
    list_filter = ('category', 'director')
    search_fields = ('name', 'description', 'director__email')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('director',)
    date_hierarchy = 'created_at'
    inlines = [ProgramLevelInline]
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('category', 'name')


@admin.register(ProgramLevel)
class ProgramLevelAdmin(admin.ModelAdmin):
    list_display = ('program', 'level_number', 'title')
    list_filter = ('program__category', 'program')
    search_fields = ('title', 'description', 'program__name')
    ordering = ('program', 'level_number')


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'mode', 'start_datetime', 'level', 'level_program')
    list_filter = ('mode', 'level__program')
    search_fields = ('title', 'level__title', 'level__program__name')  # ← updated
    list_select_related = ('level',)
    ordering = ('start_datetime',)

    def level_program(self, obj):
        return obj.level.program
    level_program.short_description = 'Program'



