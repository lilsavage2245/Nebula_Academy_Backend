# module/models.py
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from common.utils import generate_unique_slug
from common.mixins import SlugModelMixin

class Module(SlugModelMixin, models.Model):
    slug_source_field = 'title'
    slug_max_length = 150

    title         = models.CharField(max_length=150)
    slug          = models.SlugField(max_length=150, unique=True, blank=True)
    description   = models.TextField(blank=True)
    # Levels this module applies to (e.g., beginner level 2, intermediate level 4)
    
    levels = models.ManyToManyField(
        'program.ProgramLevel',
        through='ModuleLevelLink',
        related_name='modules',
        help_text='Program levels this module belongs to'
    )
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)
    is_standalone = models.BooleanField(default=False, help_text="Can be taken without full program enrollment")

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

class ModuleLevelLink(models.Model):
    module = models.ForeignKey('Module', on_delete=models.CASCADE)
    level = models.ForeignKey('program.ProgramLevel', on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        unique_together = ('module', 'level')
        ordering = ['level', 'order']

class ModuleLecturer(models.Model):
    module   = models.ForeignKey(Module, on_delete=models.CASCADE)
    lecturer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role     = models.CharField(max_length=50, blank=True)  # e.g., "Primary", "Assistant"

    class Meta:
        unique_together = ('module', 'lecturer')



class LectureMaterial(models.Model):
    AUDIENCE_CHOICES = [
        ('FREE', 'Free Users'),
        ('ENROLLED', 'Enrolled Students')
    ]

    module       = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='materials')
    description = models.TextField(blank=True)
    is_downloadable = models.BooleanField(default=True)
    audience     = models.CharField(max_length=8, choices=AUDIENCE_CHOICES)
    title        = models.CharField(max_length=150)
    slides       = models.FileField(upload_to='modules/slides/')
    video_url    = models.URLField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.module.title} — {self.title}"

class EvaluationComponent(models.Model):
    COMPONENT_TYPES = [
        ('QUIZ', 'Quiz'),
        ('EXAM', 'Exam'),
        ('PROJECT', 'Project')
    ]

    module       = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='evaluations')
    type         = models.CharField(max_length=7, choices=COMPONENT_TYPES)
    title        = models.CharField(max_length=150)
    is_required   = models.BooleanField(default=True, help_text='Is this component mandatory for module completion')
    max_score   = models.PositiveIntegerField(default=100, help_text='Maximum score for this component')
    deadline     = models.DateTimeField(null=True, blank=True, help_text='Deadline for submission')
    criteria     = models.JSONField(default=dict, help_text='Pass criteria JSON schema')
    weight       = models.DecimalField(max_digits=5, decimal_places=2, default=1.0,
                        help_text='Relative weight of this component for module completion')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['type', 'title']

    def __str__(self):
        return f"{self.get_type_display()} — {self.module.title}: {self.title}"
