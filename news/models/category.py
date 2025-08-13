# news/models/category.py
from django.db import models
from common.mixins import SlugModelMixin

class NewsCategory(SlugModelMixin, models.Model):
    slug_source_field = 'name'
    slug_max_length = 100

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True, help_text="Optional CSS icon class or emoji")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
