# certificate/models.py
from django.db import models
from django.conf import settings
from common.mixins import SlugModelMixin
from django.utils.text import slugify
from django.utils import timezone


class CertificateType(models.TextChoices):
    PROGRAM_COMPLETION = 'PROGRAM_COMPLETION', 'Program Completion'
    MODULE_COMPLETION = 'MODULE_COMPLETION', 'Module Completion'
    MERIT = 'MERIT', 'Special Recognition'
    PARTICIPATION = 'PARTICIPATION', 'Participation'


class CertificateTemplate(SlugModelMixin, models.Model):
    slug_source_field = 'title'
    slug_max_length = 100

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    certificate_type = models.CharField(
        max_length=30,
        choices=CertificateType.choices,
        default=CertificateType.PROGRAM_COMPLETION
    )
    background_image = models.ImageField(
        upload_to='certificates/backgrounds/',
        null=True,
        blank=True,
        help_text="Optional certificate background"
    )
    layout_config = models.JSONField(
        default=dict,
        help_text="Positioning info for name, date, program, etc."
    )
    criteria = models.JSONField(
        default=dict,
        help_text="e.g., {'modules_required': 3, 'min_score': 80}"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} ({self.get_certificate_type_display()})"


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
        null=True,
        blank=True
    )
    certificate_type = models.CharField(
        max_length=30,
        choices=CertificateType.choices
    )
    program = models.ForeignKey(
        'program.ProgramLevel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_certificates'
    )
    module = models.ForeignKey(
        'module.Module',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='module_certificates'
    )
    awarded_on = models.DateTimeField(default=timezone.now)
    certificate_id = models.CharField(max_length=50, unique=True)
    file = models.FileField(
        upload_to='certificates/generated/',
        null=True,
        blank=True,
        help_text="Optional: Path to generated certificate PDF"
    )
    is_downloaded = models.BooleanField(default=False)
    downloaded_on = models.DateTimeField(null=True, blank=True)

    revoked = models.BooleanField(default=False)
    revoked_on = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates_revoked'
    )

    class Meta:
        ordering = ['-awarded_on']

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
