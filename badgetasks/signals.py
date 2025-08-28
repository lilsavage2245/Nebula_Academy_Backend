# badgetasks/signals.py
from __future__ import annotations
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import User
from badgetasks.models import WeeklyTask, WeeklyTaskAssignment
from badgetasks.utils import current_week_bounds, target_from_task


def _pick_initial_tasks_for(user: User, limit: int = 3):
    """
    Simple deterministic pick for onboarding: first N active tasks
    matching the user's audience (BOTH or user's role), ordered by code.
    You can swap this for a richer chooser later.
    """
    audience_codes = ["BOTH", user.role]
    return (WeeklyTask.objects
            .filter(is_active=True, audience__in=audience_codes)
            .order_by("code")[:limit])


@receiver(post_save, sender=User)
def assign_weekly_tasks_on_user_creation(sender, instance: User, created: bool, **kwargs):
    """
    On first creation of an active FREE/ENROLLED user, assign up to 3 tasks
    for the current week, with week bounds and target set properly.
    """
    if not created:
        return
    if not instance.is_active:
        return
    if instance.role not in (User.Roles.FREE, User.Roles.ENROLLED):
        return

    week_start, week_end = current_week_bounds()
    tasks = _pick_initial_tasks_for(instance, limit=3)

    with transaction.atomic():
        for task in tasks:
            tgt = target_from_task(task)
            WeeklyTaskAssignment.objects.get_or_create(
                user=instance,
                task=task,
                week_start=week_start,  # ← NEW: scope to this week
                defaults={
                    "week_end": week_end,
                    "target": tgt,
                    "current": 0,
                    "status": WeeklyTaskAssignment.Status.PENDING,
                    "progress": {"target": tgt},
                },
            )
