# certificate/admin.py
from django.contrib import admin
from django.utils import timezone
from .models import CertificateTemplate, UserCertificate, CertificateType, Grade


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "certificate_type", "program", "is_active", "created_at")
    list_filter = ("certificate_type", "program", "is_active")
    search_fields = ("title", "program__name")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("certificate_type", "title")


# --- Admin actions for issued certificates ---
@admin.action(description="Revoke selected certificates")
def revoke_selected(modeladmin, request, queryset):
    now = timezone.now()
    updated = queryset.filter(revoked=False).update(revoked=True, revoked_on=now, status="REVOKED")
    modeladmin.message_user(request, f"Revoked {updated} certificate(s).")

@admin.action(description="Unrevoke selected certificates")
def unrevoke_selected(modeladmin, request, queryset):
    updated = queryset.filter(revoked=True).update(revoked=False, revoked_on=None, revoked_by=None, status="ISSUED")
    modeladmin.message_user(request, f"Unrevoked {updated} certificate(s).")

@admin.action(description="Clear PDF file (force re-render later)")
def clear_pdf(modeladmin, request, queryset):
    count = 0
    for uc in queryset:
        if uc.pdf_file:
            uc.pdf_file.delete(save=False)
            uc.pdf_file = None
            uc.save(update_fields=["pdf_file"])
            count += 1
    modeladmin.message_user(request, f"Cleared PDF for {count} certificate(s).")


@admin.register(UserCertificate)
class UserCertificateAdmin(admin.ModelAdmin):
    """
    Matches the upgraded UserCertificate:
      - FKs: user, template, program, issued_by, revoked_by
      - M2M: modules
      - Fields: serial, verify_token, grade, session_label, year_of_completion,
                completed_at, awarded_on, pdf_file, status, revoked, revoked_on
    """
    list_display = (
        "user",
        "program",
        "grade",
        "session_label",
        "year_of_completion",
        "serial",
        "status",
        "awarded_on",
        "revoked",
    )
    list_filter = (
        "program",
        "grade",
        "status",
        "revoked",
        "year_of_completion",
        ("issued_by", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        "serial",
        "verify_token",
        "user__email",
        "user__first_name",
        "user__last_name",
        "template__title",
        "program__name",
    )
    date_hierarchy = "awarded_on"
    ordering = ("-awarded_on",)

    list_select_related = ("user", "template", "program", "issued_by", "revoked_by")
    autocomplete_fields = ("user", "template", "program", "modules", "issued_by", "revoked_by")

    readonly_fields = ("serial", "verify_token", "awarded_on", "revoked_on")

    fieldsets = (
        ("Identity", {
            "fields": ("user", "program", "template", "certificate_type")
        }),
        ("Academic", {
            "fields": ("modules", "specialization_label", "grade", "session_label", "year_of_completion", "completed_at")
        }),
        ("Issuance", {
            "fields": ("serial", "verify_token", "status", "awarded_on", "issued_by", "pdf_file")
        }),
        ("Revocation", {
            "fields": ("revoked", "revoked_on", "revoked_by")
        }),
        ("Metadata", {
            "classes": ("collapse",),
            "fields": ("meta",),
        }),
    )

    actions = [revoke_selected, unrevoke_selected, clear_pdf]
