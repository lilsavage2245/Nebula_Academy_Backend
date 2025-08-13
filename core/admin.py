# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserActivityLog

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'first_name', 'last_name', 'role', 'program_category', 'program_level', 'is_active', 'school_email_verified')
    list_filter = ('role', 'program_category', 'program_level', 'is_active', 'school_email_verified', 'date_joined')
    raw_id_fields = ('program_level',)

    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'slug', 'profile_picture', 'location')}),
        ('Program Placement', {'fields': ('role', 'program_category', 'program_level')}),
        ('Status', {'fields': ('school_email_verified', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined', 'password_changed_at')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
        ('Preferences', {'fields': ('theme_preference', 'personalised_class_filter')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'program_category', 'program_level', 'password1', 'password2')}
        ),
    )


    readonly_fields = ('slug', 'date_joined')

@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'ip_address', 'timestamp', 'user_agent', 'device_type']
    search_fields = ['user__email', 'action']
    list_filter = ['action', 'timestamp']
