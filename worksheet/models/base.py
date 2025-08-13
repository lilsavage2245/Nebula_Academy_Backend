# worksheet/models/base.py
from django.db import models

class WorksheetAudience(models.TextChoices):
    ENROLLED = 'ENROLLED', 'Enrolled Students Only'
    FREE = 'FREE', 'Free Users'
    BOTH = 'BOTH', 'Both Enrolled and Free Users'

class SubmissionStatus(models.TextChoices):
    SUBMITTED = 'SUBMITTED', 'Submitted'
    REVIEWED = 'REVIEWED', 'Reviewed'
    RESUBMITTED = 'RESUBMITTED', 'Resubmitted'

class WorksheetFormat(models.TextChoices):
    FILE = 'FILE', 'File Upload'
    LINK = 'LINK', 'External Link'
    INTERACTIVE = 'INTERACTIVE', 'Interactive Form'
