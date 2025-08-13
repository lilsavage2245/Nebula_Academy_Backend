# applications/models.py
from django.db import models
from django.conf import settings
from program.models import Program
from module.models import Module

class ApplicationStatus(models.TextChoices):
    PENDING   = 'PENDING', 'Pending'
    REVIEWED  = 'REVIEWED', 'Reviewed'
    ACCEPTED  = 'ACCEPTED', 'Accepted'
    REJECTED  = 'REJECTED', 'Rejected'
    WITHDRAWN = 'WITHDRAWN', 'Withdrawn'


class ProgramApplication(models.Model):
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='program_applications')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='applications')
    level = models.ForeignKey('program.ProgramLevel', on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=10, choices=ApplicationStatus.choices, default=ApplicationStatus.PENDING)
    applicant_note = models.TextField(blank=True, help_text="Why do you want to join this program?")
    supporting_documents = models.FileField(upload_to='applications/docs/', blank=True, null=True)

    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='program_reviews')
    review_comment = models.TextField(blank=True)
    
    submitted_on = models.DateTimeField(auto_now_add=True)
    reviewed_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('applicant', 'program')
        ordering = ['-submitted_on']

    def __str__(self):
        return f"{self.applicant.email} → {self.program.name} ({self.status})"


class ModuleApplication(models.Model):
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='module_applications')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='applications')

    status = models.CharField(max_length=10, choices=ApplicationStatus.choices, default=ApplicationStatus.PENDING)
    applicant_note = models.TextField(blank=True, help_text="Why do you want to join this module?")
    
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='module_reviews')
    review_comment = models.TextField(blank=True)
    
    submitted_on = models.DateTimeField(auto_now_add=True)
    reviewed_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('applicant', 'module')
        ordering = ['-submitted_on']

    def __str__(self):
        return f"{self.applicant.email} → {self.module.title} ({self.status})"
