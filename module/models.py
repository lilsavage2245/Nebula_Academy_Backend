# module/models.py
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from common.mixins import SlugModelMixin
from django.core.exceptions import ValidationError
import uuid

class Module(SlugModelMixin, models.Model):
    slug_source_field = 'title'
    slug_max_length = 150

    title           = models.CharField(max_length=150)
    slug            = models.SlugField(max_length=150, unique=True, blank=True)
    description     = models.TextField(blank=True)
    prerequisites   = models.TextField(blank=True)
    tools_software  = models.JSONField(default=list, blank=True)  # e.g. ["VS Code","Python 3.12","Node 20"]

    levels = models.ManyToManyField(
        'program.ProgramLevel',
        through='ModuleLevelLink',
        related_name='modules',
        help_text='Program levels this module belongs to'
    )
    is_standalone   = models.BooleanField(default=False, help_text="Can be taken without full program enrollment")
    is_active       = models.BooleanField(default=True)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.title


class ModuleLevelLink(models.Model):
    module = models.ForeignKey('Module', on_delete=models.CASCADE)
    level  = models.ForeignKey('program.ProgramLevel', on_delete=models.CASCADE)
    order  = models.PositiveSmallIntegerField(default=1)

    class Meta:
        unique_together = ('module', 'level')
        ordering = ['level', 'order']


class ModuleLecturer(models.Model):
    module   = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lecturers')
    lecturer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role     = models.CharField(max_length=50, blank=True)  # e.g., "Primary", "Assistant"

    class Meta:
        unique_together = ('module', 'lecturer')


class EvaluationComponent(models.Model):
    COMPONENT_TYPES = [
        ('QUIZ', 'Quiz'),
        ('EXAM', 'Exam'),
        ('PROJECT', 'Project')
    ]

    module        = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='evaluations')
    type          = models.CharField(max_length=7, choices=COMPONENT_TYPES)
    title         = models.CharField(max_length=150)
    is_required   = models.BooleanField(default=True, help_text='Is this component mandatory for module completion')
    max_score     = models.PositiveIntegerField(default=100, help_text='Maximum score for this component')
    deadline      = models.DateTimeField(null=True, blank=True, help_text='Deadline for submission')
    criteria      = models.JSONField(default=dict, help_text='Pass criteria JSON schema')
    weight        = models.DecimalField(max_digits=5, decimal_places=2, default=1.0,
                        help_text='Relative weight of this component for module completion')

    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['type', 'title']
        indexes = [
            models.Index(fields=['module', 'type']),
        ]

    def __str__(self):
        return f"{self.get_type_display()} — {self.module.title}: {self.title}"


class MaterialAudience(models.TextChoices):
    FREE = "FREE", "Free Users"
    ENROLLED = "ENROLLED", "Enrolled Students"
    BOTH = "BOTH", "Both"


class MaterialType(models.TextChoices):
    PDF   = "PDF", "PDF"
    SLIDES = "SLIDES", "Slides"
    LINK  = "LINK", "External Link"
    OTHER = "OTHER", "Other"


def module_material_upload_to(instance, filename):
    # e.g. module_materials/<module-slug>/<uuid>-<filename>
    return f"module_materials/{instance.module.slug}/{uuid.uuid4()}-{filename}"


class ModuleMaterial(models.Model):
    module        = models.ForeignKey("module.Module", on_delete=models.CASCADE, related_name="materials")
    title         = models.CharField(max_length=150)
    slug          = models.SlugField(max_length=160, blank=True)  # stable nested route: /modules/<module>/materials/<slug>/
    description   = models.TextField(blank=True)

    audience      = models.CharField(max_length=8, choices=MaterialAudience.choices, default=MaterialAudience.ENROLLED)
    type          = models.CharField(max_length=10, choices=MaterialType.choices, default=MaterialType.PDF)

    file          = models.FileField(upload_to=module_material_upload_to, blank=True, null=True)
    external_url  = models.URLField(blank=True, null=True)

    # Optional but helpful for UI/policy
    content_type  = models.CharField(max_length=100, blank=True)  # e.g. "application/pdf"
    file_size     = models.PositiveIntegerField(null=True, blank=True)  # bytes

    version       = models.CharField(max_length=32, blank=True, help_text="e.g. v1.0 or 2025-08-17")
    is_active     = models.BooleanField(default=True)

    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        unique_together = (("module", "slug"),)
        indexes = [
            models.Index(fields=["module", "slug"]),
            models.Index(fields=["module", "type"]),
            models.Index(fields=["module", "audience"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.module.title} — {self.title}"

    def save(self, *args, **kwargs):
        # generate slug once from title for stable URLs
        if not self.slug:
            base = slugify(self.title)[:120] or uuid.uuid4().hex[:8]
            self.slug = f"{base}-{uuid.uuid4().hex[:6]}"
        # auto-fill content_type / file_size if available
        if self.file and hasattr(self.file, "file"):
            try:
                self.file_size = getattr(self.file.file, "size", None) or self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    def clean(self):
        """Ensure material source matches its type and avoid invalid combos."""
        has_file = bool(self.file)
        has_link = bool(self.external_url)

        # Must provide exactly one source for most types
        if self.type in (MaterialType.PDF, MaterialType.SLIDES, MaterialType.OTHER):
            if not has_file and not has_link:
                raise ValidationError("Provide a file or an external_url for this material type.")
        if self.type == MaterialType.LINK:
            if not has_link:
                raise ValidationError("LINK material must have an external_url.")
            if has_file:
                raise ValidationError("LINK material should not include a file.")

        # Optional: enforce audience policy (e.g., FREE must not be exam solutions)
        # if self.title.lower().startswith("solution") and self.audience == MaterialAudience.FREE:
        #     raise ValidationError("Solution materials cannot be FREE.")

    @property
    def is_downloadable(self) -> bool:
        # derive from presence of file
        return bool(self.file)

    @property
    def is_link(self) -> bool:
        return bool(self.external_url)
