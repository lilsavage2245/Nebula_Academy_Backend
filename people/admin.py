# people/admin.py
from django.contrib import admin
from django.utils import timezone

from .models import (
    Expertise,
    LecturerProfile,
    ProgramDirectorProfile,
    VolunteerProfile,
    BloggerProfile,
    PartnerProfile,
    OnboardingSurvey,
)

# ---------- Reusable base admin for profile models ----------

@admin.action(description="Approve selected profiles")
def approve_selected(modeladmin, request, queryset):
    updated = queryset.update(is_verified=True, approved_on=timezone.now(), approved_by=request.user)
    modeladmin.message_user(request, f"Approved {updated} profile(s).")

@admin.action(description="Unapprove selected profiles")
def unapprove_selected(modeladmin, request, queryset):
    updated = queryset.update(is_verified=False, approved_on=None, approved_by=None)
    modeladmin.message_user(request, f"Unapproved {updated} profile(s).")

class BaseProfileAdmin(admin.ModelAdmin):
    """
    Shared config for Lecturer/Director/Volunteer/Blogger/Partner profiles.
    """
    list_display = (
        "user",
        "is_verified",
        "approved_by",
        "approved_on",
        "created_at",
    )
    list_filter = (
        "is_verified",
        "created_at",
        "approved_on",
    )
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "slug",
    )
    autocomplete_fields = ("user", "approved_by")
    readonly_fields = ("slug", "created_at", "updated_at", "approved_on")
    actions = [approve_selected, unapprove_selected]

    fieldsets = (
        (None, {
            "fields": ("user", "bio", "profile_image", "tags")
        }),
        ("Links", {
            "fields": ("website", "linkedin", "twitter", "github"),
            "classes": ("collapse",),
        }),
        ("Moderation", {
            "fields": ("is_verified", "approved_by", "approved_on"),
        }),
        ("System", {
            "fields": ("slug", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

# ---------- Concrete admins ----------

@admin.register(Expertise)
class ExpertiseAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)

@admin.register(LecturerProfile)
class LecturerProfileAdmin(BaseProfileAdmin):
    # Extra fields for lecturers
    filter_horizontal = ("expertise",)
    fieldsets = BaseProfileAdmin.fieldsets[:1] + (
        ("Lecturer Details", {
            "fields": ("expertise", "qualifications", "office_hours"),
        }),
    ) + BaseProfileAdmin.fieldsets[1:]

@admin.register(ProgramDirectorProfile)
class ProgramDirectorProfileAdmin(BaseProfileAdmin):
    fieldsets = BaseProfileAdmin.fieldsets[:1] + (
        ("Director Details", {
            "fields": ("department", "office_hours"),
        }),
    ) + BaseProfileAdmin.fieldsets[1:]

@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(BaseProfileAdmin):
    fieldsets = BaseProfileAdmin.fieldsets[:1] + (
        ("Volunteer Details", {
            "fields": ("interests", "availability"),
        }),
    ) + BaseProfileAdmin.fieldsets[1:]

@admin.register(BloggerProfile)
class BloggerProfileAdmin(BaseProfileAdmin):
    fieldsets = BaseProfileAdmin.fieldsets[:1] + (
        ("Blogger Details", {
            "fields": ("pen_name",),
        }),
    ) + BaseProfileAdmin.fieldsets[1:]

@admin.register(PartnerProfile)
class PartnerProfileAdmin(BaseProfileAdmin):
    fieldsets = BaseProfileAdmin.fieldsets[:1] + (
        ("Partner Details", {
            "fields": ("organization", "partnership_level"),
        }),
    ) + BaseProfileAdmin.fieldsets[1:]

# ---------- Onboarding / FREE registration survey ----------

@admin.register(OnboardingSurvey)
class OnboardingSurveyAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "created_at",
        "country",
        "referral_source",
        "age_range",
        "accept_terms",
        "accept_privacy",
        "email_opt_in",
        "is_latest",
    )
    list_filter = (
        "is_latest",
        "referral_source",
        "age_range",
        "accept_terms",
        "accept_privacy",
        "email_opt_in",
        "created_at",
    )
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "motivation_text",
        "phone",
        "country",
    )
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "terms_accepted_at", "privacy_accepted_at")
    fieldsets = (
        ("User & Timing", {
            "fields": ("user", "created_at", "is_latest")
        }),
        ("Profile", {
            "fields": ("age_range", "phone", "country", "interest_areas", "motivation_text", "referral_source")
        }),
        ("Consents", {
            "fields": (
                "accept_terms", "terms_version", "terms_accepted_at",
                "accept_privacy", "privacy_version", "privacy_accepted_at",
                "email_opt_in", "info_accuracy_confirmed",
            )
        }),
        ("Analytics", {
            "classes": ("collapse",),
            "fields": ("utm",),
        }),
    )
    ordering = ("-created_at",)

