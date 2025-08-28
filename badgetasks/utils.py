# badgetasks/utils.py
from __future__ import annotations
from datetime import timedelta, date
from typing import Tuple, Optional

from django.utils.timezone import now
from django.db.models import Q

# Import here (not at module top) if you ever hit circular imports in tests.
from badgetasks.models import WeeklyTask, WeeklyTaskAssignment


# --- Week helpers -------------------------------------------------------------

def current_week_bounds(today: Optional[date] = None) -> Tuple[date, date]:
    """
    Return (monday_date, sunday_date) for the week containing `today`.
    Uses server tz. Prefer setting TIME_ZONE='Europe/London' in settings.
    """
    today = (today or now()).date()
    monday = today - timedelta(days=today.weekday())  # 0=Mon
    sunday = monday + timedelta(days=6)
    return monday, sunday


def week_bounds_for(d: date) -> Tuple[date, date]:
    """Same as current_week_bounds, but explicit date param."""
    return current_week_bounds(d)


def within_week(dt, week_start: date, week_end: date) -> bool:
    """True if a timezone-aware datetime `dt` falls within the [week_start, week_end] date window."""
    if not dt:
        return False
    d = dt.date()
    return week_start <= d <= week_end


# --- Display / formatting helpers --------------------------------------------

def minutes_str(total_minutes: int) -> str:
    """Format minutes as 'Xh Ym'."""
    total_minutes = int(total_minutes or 0)
    return f"{total_minutes // 60}h {total_minutes % 60}m"


# --- Targets & classification -------------------------------------------------

def target_from_task(task: WeeklyTask) -> int:
    """
    Unified target resolver:
    - TIME_SPENT: prefer task.target_count (minutes). Fallback to required_hours * 60 for legacy.
    - Others: task.target_count (count).
    """
    if task.task_type == WeeklyTask.TaskType.TIME_SPENT:
        return task.target_count or (task.required_hours or 0) * 60
    return task.target_count or 1


def classify_segment(
    lifetime_active_minutes: int,
    weekly_active_minutes: int,
) -> str:
    """
    Classify a user into NEWBIE / RAMPING / ENGAGED using simple thresholds.
    Adjust as needed.
    """
    # Weekly has priority; then lifetime as fallback
    if weekly_active_minutes >= 240 or lifetime_active_minutes >= 480:  # 4h this week OR 8h lifetime
        return WeeklyTask.MinSegment.ENGAGED
    if weekly_active_minutes >= 60 or lifetime_active_minutes >= 120:   # 1h this week OR 2h lifetime
        return WeeklyTask.MinSegment.RAMPING
    return WeeklyTask.MinSegment.NEWBIE


# --- Cooldown / rotation -----------------------------------------------------

def cooldown_active(user, task_code: str, week_start: date, cooldown_weeks: int) -> bool:
    """
    True if `task_code` was assigned to `user` within the last `cooldown_weeks`
    (including the current week), so we should skip re-assigning it.
    """
    if cooldown_weeks <= 0:
        return False
    earliest = week_start - timedelta(weeks=cooldown_weeks)
    return WeeklyTaskAssignment.objects.filter(
        user=user,
        task__code=task_code,
        week_start__gte=earliest,
        week_start__lte=week_start,
    ).exists()


def last_assigned_week(user, task_code: str) -> Optional[date]:
    """
    Return the most recent week_start when this task_code was assigned to user, or None.
    Useful for analytics or debugging rotations.
    """
    row = (WeeklyTaskAssignment.objects
           .filter(user=user, task__code=task_code)
           .order_by('-week_start')
           .values('week_start')
           .first())
    return row['week_start'] if row else None
