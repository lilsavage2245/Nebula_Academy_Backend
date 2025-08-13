# enrollments/models.py
from django.db import models
from django.conf import settings
from program.models import Program, ProgramLevel

class Enrollment(models.Model):
    """
    Represents a student’s enrollment in a Program. One active at a time.
    """
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='active_enrollment'
    )
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='enrollments')
    
    class Status(models.TextChoices):
        ACTIVE    = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        DROPPED   = 'DROPPED', 'Dropped'
    
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    enrolled_on = models.DateTimeField(auto_now_add=True)
    completed_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'program')

    def __str__(self):
        return f"{self.student.get_full_name()} in {self.program} ({self.status})"


class StudentProgramProgress(models.Model):
    """
    Tracks student's level progress within a program.
    """
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='progress'
    )
    level = models.ForeignKey(
        ProgramLevel,
        on_delete=models.CASCADE,
        related_name='student_progress'
    )
    started_on = models.DateField(auto_now_add=True)
    completed_on = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('enrollment', 'level')
        ordering = ['level__level_number']

    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} — Level {self.level.level_number}"

class ModuleProgress(models.Model):
    enrollment   = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='module_progress')
    module       = models.ForeignKey('modules.Module', on_delete=models.CASCADE)
    completed    = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('enrollment', 'module')

    def __str__(self):
        return f"{self.enrollment.student} - {self.module.title} ({'Done' if self.completed else 'In Progress'})"


class FreeStudentProfile(models.Model):
    """
    Stores data for free-access users who are not formally enrolled.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='free_profile'
    )
    selected_category = models.CharField(
        max_length=3,
        choices=Program.Category.choices
    )
    selected_level_number = models.PositiveSmallIntegerField()

    date_joined = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} (Free — {self.selected_category} L{self.selected_level_number})"
