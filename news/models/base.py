# news/models/base.py
from django.db import models

class Status(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PUBLISHED = 'PUBLISHED', 'Published'
    PENDING = 'PENDING', 'Pending Approval'
