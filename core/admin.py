# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserActivityLog

# If people app is installed with OnboardingSurvey:
try:
    from people.models import OnboardingSurvey
except Exception:
    OnboardingSurvey = None

if OnboardingSurvey:
    class LatestOnboardingInline(admin.StackedInline):
        model = OnboardingSurvey
        extra = 0
        max_num = 1
        can_delete = False
        readonly_fields = ("created_at",)
        fields = (
            "age_range", "phone", "country", "interest_areas", "motivation_text",
            "referral_source", "accept_terms", "email_opt_in", "info_accuracy_confirmed",
            "utm", "created_at", "is_latest",
        )

        def get_queryset(self, request):
            qs = super().get_queryset(request)
            return qs.filter(is_latest=True)
else:
    LatestOnboardingInline = None


class UserAdmin(BaseUserAdmin):
    model = User
    list_display = (
        'email', 'first_name', 'last_name', 'role',
        'program_category', 'program_level',
        'is_active', 'school_email_verified'
    )
    list_filter = (
        'role', 'program_category', 'program_level',
        'is_active', 'school_email_verified', 'date_joined'
    )
    ordering = ('-date_joined',)
    search_fields = ('email', 'first_name', 'last_name')

    raw_id_fields = ('program_level',)
    readonly_fields = ('slug', 'date_joined')

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
            'fields': (
                'email', 'first_name', 'last_name', 'role',
                'program_category', 'program_level',
                'password1', 'password2'
            )
        }),
    )

    if LatestOnboardingInline:
        inlines = [LatestOnboardingInline]


# Safely replace any existing registration
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'ip_address', 'timestamp', 'user_agent', 'device_type']
    search_fields = ['user__email', 'action']
    list_filter = ['action', 'timestamp']