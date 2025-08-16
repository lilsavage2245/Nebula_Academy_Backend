# application/admin.py
from django.contrib import admin
from .models import Application, ApplicationEvent, ApplicationReview, ApplicationStatus, ApplicationType


class ApplicationEventInline(admin.TabularInline):
    model = ApplicationEvent
    extra = 0
    readonly_fields = ("action", "payload", "actor", "created_at")
    can_delete = False
    show_change_link = False


class ApplicationReviewInline(admin.TabularInline):
    model = ApplicationReview
    extra = 0
    autocomplete_fields = ("reviewer",)
    readonly_fields = ("created_at",)


@admin.action(description="Mark selected as UNDER_REVIEW")
def mark_under_review(modeladmin, request, queryset):
    for app in queryset:
        app.set_status(ApplicationStatus.UNDER_REVIEW, actor=request.user)
    modeladmin.message_user(request, f"Moved {queryset.count()} application(s) to UNDER_REVIEW.")


@admin.action(description="Accept selected applications")
def accept_selected(modeladmin, request, queryset):
    for app in queryset:
        app.set_status(ApplicationStatus.ACCEPTED, actor=request.user)
    modeladmin.message_user(request, f"Accepted {queryset.count()} application(s).")


@admin.action(description="Reject selected applications")
def reject_selected(modeladmin, request, queryset):
    for app in queryset:
        app.set_status(ApplicationStatus.REJECTED, actor=request.user)
    modeladmin.message_user(request, f"Rejected {queryset.count()} application(s).")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant", "type", "program", "level", "module", "status", "submitted_on", "reviewed_on")
    list_filter  = ("type", "status", "program", "submitted_on", "reviewed_on")
    search_fields = ("applicant__email", "program__name", "module__title")
    autocomplete_fields = ("applicant", "program", "level", "module", "reviewer")
    date_hierarchy = "submitted_on"
    ordering = ("-submitted_on",)

    inlines = [ApplicationReviewInline, ApplicationEventInline]
    actions = [mark_under_review, accept_selected, reject_selected]

    fieldsets = (
        ("Applicant", {"fields": ("applicant",)}),
        ("Type & Target", {"fields": ("type", "program", "level", "module")}),
        ("Status", {"fields": ("status", "submitted_on", "reviewed_on")}),
        ("Review", {"fields": ("reviewer", "review_comment")}),
        ("Applicant Note & Docs", {"fields": ("applicant_note", "supporting_documents")}),
        ("Form Snapshot", {"classes": ("collapse",), "fields": ("form_key", "answers")}),
        ("Meta", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("submitted_on", "reviewed_on", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        # Log submit if transitioning from DRAFT to SUBMITTED via admin save
        if change:
            old = Application.objects.get(pk=obj.pk)
            if old.status == ApplicationStatus.DRAFT and obj.status == ApplicationStatus.SUBMITTED:
                ApplicationEvent.log(obj, request.user, "SUBMITTED", {})
        super().save_model(request, obj, form, change)


@admin.register(ApplicationEvent)
class ApplicationEventAdmin(admin.ModelAdmin):
    list_display = ("application", "action", "actor", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("application__applicant__email", "action")
    autocomplete_fields = ("application", "actor")
    readonly_fields = ("application", "actor", "action", "payload", "created_at")
    ordering = ("-created_at",)


@admin.register(ApplicationReview)
class ApplicationReviewAdmin(admin.ModelAdmin):
    list_display = ("application", "reviewer", "score", "created_at")
    list_filter = ("created_at",)
    search_fields = ("application__applicant__email", "reviewer__email")
    autocomplete_fields = ("application", "reviewer")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
