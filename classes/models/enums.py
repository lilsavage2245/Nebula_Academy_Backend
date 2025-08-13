# enums.py
from django.db import models

class LessonAudience(models.TextChoices):
    FREE = 'FREE', 'Free Users'
    ENROLLED = 'ENROLLED', 'Enrolled Students'
    BOTH = 'BOTH', 'Both Free and Enrolled Users'
    STAFF = 'STAFF', 'Academy Staff Only'

class MaterialAudience(models.TextChoices):
    FREE = 'FREE', 'Free Users'
    ENROLLED = 'ENROLLED', 'Enrolled Students'
    BOTH = 'BOTH', 'Both Free and Enrolled Users'
    STAFF = 'STAFF', 'Academy Staff Only'
