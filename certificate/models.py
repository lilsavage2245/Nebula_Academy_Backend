# certificate/models.py
from django.db import models
from django.conf import settings
from common.mixins import SlugModelMixin
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Q


class CertificateType(models.TextChoices):
    PROGRAM_COMPLETION = 'PROGRAM_COMPLETION', 'Program Completion'
    MODULE_COMPLETION  = 'MODULE_COMPLETION',  'Module Completion'
    MERIT              = 'MERIT',              'Special Recognition'
    PARTICIPATION      = 'PARTICIPATION',      'Participation'


class CertificateTemplate(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    certificate_type = models.CharField(
        max_length=30,
        choices=CertificateType.choices,
        default=CertificateType.PROGRAM_COMPLETION
    )

    # NEW: tie template to a Program (only if relevant, e.g., program completion)
    program = models.ForeignKey(
        'program.Program',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='certificate_templates',
        help_text="For PROGRAM_COMPLETION templates, link the owning Program."
    )

    background_image = models.ImageField(upload_to='certificates/backgrounds/', null=True, blank=True)
    layout_config = models.JSONField(default=dict, help_text="Positioning info for name, date, program, etc.")
    criteria = models.JSONField(default=dict, help_text="e.g., {'levels_required': 'ALL', 'min_gpa': 4.0}")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        constraints = [
            # At most one PROGRAM_COMPLETION template per program
            models.UniqueConstraint(
                fields=['program'],
                condition=Q(certificate_type='PROGRAM_COMPLETION'),
                name='uniq_program_completion_template_per_program',
            )
        ]

    def __str__(self):
        suffix = f" — {self.program.name}" if self.program_id else ""
        return f"{self.title} ({self.get_certificate_type_display()}){suffix}"

class Grade(models.TextChoices):
    FIRST          = "FIRST",           "First Class"
    SECOND_UPPER   = "SECOND_UPPER",    "Second Class Upper"
    SECOND_LOWER   = "SECOND_LOWER",    "Second Class Lower"
    DISTINCTION    = "DISTINCTION",     "Distinction"
    MERIT          = "MERIT",           "Merit"
    PASS           = "PASS",            "Pass"
    UNGRADED       = "UNGRADED",        "Ungraded"


class UserCertificate(models.Model):
    """
    Issued certificate to a specific user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates'
    )
    template = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    certificate_type = models.CharField(max_length=30, choices=CertificateType.choices)

    # CHANGE: point to Program (not ProgramLevel)
    program = models.ForeignKey(
        'program.Program',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='issued_certificates'
    )

    # Modules that formed the specialization (optional but useful)
    modules = models.ManyToManyField(
        'module.Module',
        blank=True,
        related_name='certificates'
    )
    # Human-friendly summary of specialization (optional; store a label snapshot)
    specialization_label = models.CharField(max_length=120, blank=True)

    # Grade, session, year
    grade = models.CharField(max_length=20, choices=Grade.choices, default=Grade.UNGRADED)
    session_label = models.CharField(max_length=64, help_text="e.g., 'Spring 2025' or '2024/2025'")
    year_of_completion = models.PositiveSmallIntegerField()
    completed_at = models.DateTimeField(help_text="When the criteria were satisfied")

    # Issuance
    awarded_on = models.DateTimeField(default=timezone.now)
    serial = models.CharField(max_length=50, unique=True)         # rename from certificate_id
    verify_token = models.CharField(max_length=64, unique=True)   # for public verification
    pdf_file = models.FileField(upload_to='certificates/generated/', null=True, blank=True)

    status = models.CharField(
        max_length=16,
        choices=[("PENDING","Pending"),("ISSUED","Issued"),("REVOKED","Revoked")],
        default="ISSUED"
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='certificates_issued'
    )

    # Freeze inputs (e.g., computed GPA, module scores) so later rubric changes don't alter history
    meta = models.JSONField(default=dict, blank=True)

    revoked = models.BooleanField(default=False)
    revoked_on = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='certificates_revoked'
    )

    class Meta:
        ordering = ['-awarded_on']
        indexes = [
            models.Index(fields=['program', 'year_of_completion']),
            models.Index(fields=['serial']),
            models.Index(fields=['verify_token']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.get_certificate_type_display()}"

    def mark_downloaded(self):
        if not self.is_downloaded:
            self.is_downloaded = True
            self.downloaded_on = timezone.now()
            self.save(update_fields=['is_downloaded', 'downloaded_on'])

    def revoke(self, by_user=None):
        if not self.revoked:
            self.revoked = True
            self.revoked_on = timezone.now()
            self.revoked_by = by_user
            self.save(update_fields=['revoked', 'revoked_on', 'revoked_by'])