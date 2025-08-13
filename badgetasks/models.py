from django.db import models
from django.conf import settings
from django.utils.timezone import now
from core.models import User  # adjust if you use custom user path


class WeeklyTask(models.Model):
    """
    Task configuration. E.g., 'Attend a lesson', 'Submit a worksheet', etc.
    """
    TASK_TYPES = [
        ('ARTICLE', 'Write and publish an article'),
        ('LESSON', 'Attend a lesson'),
        ('TIME_SPENT', 'Accumulate X hours of learning'),
        ('QUIZ', 'Complete a quiz'),
        ('WORKSHEET', 'Submit a worksheet'),
    ]

    title = models.CharField(max_length=255)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    required_hours = models.PositiveIntegerField(default=0, help_text="For TIME_SPENT task type only")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_task_type_display()} — {self.title}"


class WeeklyTaskAssignment(models.Model):
    """
    User-specific assignment of weekly tasks — could be generated dynamically each week.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_tasks')
    task = models.ForeignKey(WeeklyTask, on_delete=models.CASCADE, related_name='assignments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    progress = models.JSONField(default=dict, blank=True)  # e.g., {"hours": 2.5}
    assigned_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'task')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.email} — {self.task.title} ({self.status})"
