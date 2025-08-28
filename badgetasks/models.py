from django.db import models
from django.conf import settings
from django.utils.timezone import now


class WeeklyTask(models.Model):
    """
    Catalog of possible weekly tasks. Concrete assignments are created per-user each week.
    """
    class TaskType(models.TextChoices):
        ARTICLE     = 'ARTICLE',     'Write and publish an article'
        LESSON      = 'LESSON',      'Attend lessons'
        TIME_SPENT  = 'TIME_SPENT',  'Accumulate learning minutes'
        QUIZ        = 'QUIZ',        'Complete a quiz'
        WORKSHEET   = 'WORKSHEET',   'Submit a worksheet'
        STREAK      = 'STREAK',      'Be active on distinct days'

    class Audience(models.TextChoices):
        FREE      = 'FREE',      'Free Users'
        ENROLLED  = 'ENROLLED',  'Enrolled Students'
        BOTH      = 'BOTH',      'Both'

    class MinSegment(models.TextChoices):
        NEWBIE   = 'NEWBIE',   'Newbie'
        RAMPING  = 'RAMPING',  'Ramping'
        ENGAGED  = 'ENGAGED',  'Engaged'

    # Identifiers/config
    code = models.SlugField(
        max_length=64,
        unique=True,
        help_text="Stable code for rotation/cooldown (e.g. t_time_300)."
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    task_type = models.CharField(max_length=20, choices=TaskType.choices)
    audience = models.CharField(max_length=10, choices=Audience.choices, default=Audience.BOTH)
    min_segment = models.CharField(
        max_length=10,
        choices=MinSegment.choices,
        blank=True,
        null=True,
        help_text="Lowest engagement segment this task applies to (optional)."
    )

    # Unified target: minutes for TIME_SPENT, counts for others
    target_count = models.PositiveIntegerField(
        default=1,
        help_text="Minutes for TIME_SPENT; count for other types (e.g., lessons=3)."
    )

    # Rotation policy
    cooldown_weeks = models.PositiveSmallIntegerField(
        default=1,
        help_text="Minimum weeks before this task can be re-assigned to the same user."
    )

    # Legacy compatibility (optional; keep if you already use it)
    required_hours = models.PositiveIntegerField(
        default=0,
        help_text="Legacy: hours for TIME_SPENT. Prefer target_count (minutes)."
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.title}"


class WeeklyTaskAssignment(models.Model):
    """
    A concrete instance of a task for a user for a specific week (Mon–Sun).
    """
    class Status(models.TextChoices):
        PENDING     = 'PENDING',     'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED   = 'COMPLETED',   'Completed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_tasks'
    )
    task = models.ForeignKey(
        WeeklyTask,
        on_delete=models.CASCADE,
        related_name='assignments'
    )

    # Week window (dates, not datetimes). Typically Monday..Sunday in Europe/London.
    week_start = models.DateField(db_index=True)
    week_end = models.DateField(db_index=True)

    # Denormalized targets/progress for fast UI
    target = models.PositiveIntegerField(
        default=1,
        help_text="Minutes for TIME_SPENT; count for other types."
    )
    current = models.PositiveIntegerField(
        default=0,
        help_text="Computed during evaluation (minutes or count)."
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    progress = models.JSONField(default=dict, blank=True)  # e.g., {"minutes": 130, "target": 300}

    assigned_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Allow the same task to be assigned again in a different week, but only once per week.
        unique_together = ('user', 'task', 'week_start')
        indexes = [
            models.Index(fields=['user', 'week_start']),
            models.Index(fields=['user', 'status', 'week_start']),
        ]
        ordering = ['-week_start', '-updated_at']

    def __str__(self):
        return f"{self.user.email} — {self.task.code} ({self.status}) {self.week_start}"

    # Convenience helpers
    def mark_progress(self, current_value: int, progress_payload: dict | None = None):
        self.current = max(0, int(current_value))
        self.progress = progress_payload or self.progress or {}
        self.progress.setdefault('target', self.target)
        if self.task.task_type == WeeklyTask.TaskType.TIME_SPENT:
            # ensure minutes key exists for UI
            self.progress.setdefault('minutes', self.current)

        if self.current >= self.target:
            self.status = WeeklyTaskAssignment.Status.COMPLETED
        elif self.current > 0:
            self.status = WeeklyTaskAssignment.Status.IN_PROGRESS
        else:
            self.status = WeeklyTaskAssignment.Status.PENDING

        self.save(update_fields=['current', 'progress', 'status', 'updated_at'])
