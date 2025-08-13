# event/models/category.py
from django.db import models
from common.mixins import SlugModelMixin

class EventCategory(SlugModelMixin, models.Model):
    slug_source_field = 'name'
    slug_max_length = 100

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Event Categories'

    def __str__(self):
        return self.name
