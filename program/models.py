# program/models.py
from django.db import models
from django.conf import settings
from common.mixins import SlugModelMixin
from django.utils.text import slugify

class ProgramCategory(models.TextChoices):
    PRE_ACADEMY = 'PRE', 'Pre‑Academy'
    BEGINNER    = 'BEG', 'Beginner'
    INTER_DIP   = 'INT', 'Intermediate Diploma'
    ADVANCED    = 'ADV', 'Advanced'

class Program(SlugModelMixin, models.Model):
    slug_source_field = 'slug_source'
    slug_max_length = 100

    name        = models.CharField(max_length=100)
    slug        = models.SlugField(max_length=100, unique=True, blank=True)
    category    = models.CharField(max_length=3, choices=ProgramCategory.choices)
    description = models.TextField(blank=True)
    director    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'LECTURER'},
        related_name='program_directed',
        blank=True
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('category', 'name')
        verbose_name = 'Program'
        verbose_name_plural = 'Programs'

    def __str__(self):
        return f"{self.get_category_display()}: {self.name}"

    @property
    def slug_source(self):
        return f"{self.name}-{self.category.lower()}"


class ProgramLevel(models.Model):
    program      = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='levels')
    level_number = models.PositiveSmallIntegerField()
    title        = models.CharField(max_length=255)
    description  = models.TextField()
    slug         = models.SlugField(max_length=140, unique=True, blank=True)  # 👈 NEW

    class Meta:
        unique_together = ('program', 'level_number')
        ordering = ['level_number']
        verbose_name = 'Program Level'
        verbose_name_plural = 'Program Levels'

    def __str__(self):
        return f"{self.program.name} — Level {self.level_number}: {self.title}"

    def _slug_base(self):
        # includes program slug + level number + trimmed title
        prog_slug = self.program.slug or slugify(self.program.name)
        return f"{prog_slug}-level-{self.level_number}-{slugify(self.title)[:40]}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = self._slug_base()
            slug = base
            i = 1
            while ProgramLevel.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Session(models.Model):
    MODE_CHOICES = [
        ('LIVE', 'Live'),
        ('REC',  'Recorded'),
    ]

    level          = models.ForeignKey(ProgramLevel, on_delete=models.CASCADE, related_name='sessions')
    title          = models.CharField(max_length=150)
    mode           = models.CharField(max_length=4, choices=MODE_CHOICES)
    start_datetime = models.DateTimeField()
    end_datetime   = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['start_datetime']
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'
    
    @property
    def program(self):
        return self.level.program

    def __str__(self):
        return f"{self.level.program.name} — {self.title} on {self.start_datetime:%Y-%m-%d %H:%M}"


