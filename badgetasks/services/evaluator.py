# badgetasks/services/evaluator.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Set

from django.db.models import Sum, Count
from django.utils.timezone import now

from badgetasks.models import WeeklyTask, WeeklyTaskAssignment
from badgetasks.utils import current_week_bounds
from classes.models import LessonAttendance

# Optional integrations (guard if these apps might be missing in some envs)
try:
    from dashboard.models import DashboardArticle
except Exception:  # pragma: no cover
    DashboardArticle = None

try:
    from worksheet.models import WorksheetSubmission
except Exception:  # pragma: no cover
    WorksheetSubmission = None

try:
    from classes.models.quiz import LessonQuizResult
except Exception:  # pragma: no cover
    LessonQuizResult = None

# If you implemented EngagementPing for activeness:
try:
    from engagement.models import EngagementPing
except Exception:  # pragma: no cover
    EngagementPing = None


def _daterange_qs_bounds(week_start, week_end, field: str):
    """
    Build filter kwargs for a DateField/DateTimeField limited to week_start..week_end inclusive.
    Handles both Date and DateTime fields using __date when appropriate.
    """
    # We generally filter by date component; using __date keeps tz edge cases simple.
    return {
        f"{field}__date__gte": week_start,
        f"{field}__date__lte": week_end,
    }


def _distinct_active_days(user, week_start, week_end) -> int:
    """
    Count distinct days with activity (streak) using EngagementPing if available,
    otherwise fall back to LessonAttendance timestamps.
    """
    if EngagementPing:
        days = (
            EngagementPing.objects
            .filter(user=user, minute__date__gte=week_start, minute__date__lte=week_end)
            .values_list("minute__date", flat=True)
            .distinct()
        )
        return len(list(days))

    # Fallback: days with any attendance
    days = (
        LessonAttendance.objects
        .filter(user=user, timestamp__date__gte=week_start, timestamp__date__lte=week_end)
        .values_list("timestamp__date", flat=True)
        .distinct()
    )
    return len(list(days))


def _active_minutes(user, week_start, week_end) -> int:
    """
    'Active minutes' for TIME_SPENT if you want to include EngagementPing minutes.
    If EngagementPing is not available, returns 0 (caller can add lesson minutes).
    """
    if not EngagementPing:
        return 0
    # Each unique user+minute row = 1 minute of active time.
    return (
        EngagementPing.objects
        .filter(user=user, minute__date__gte=week_start, minute__date__lte=week_end)
        .count()
    )


def evaluate_weekly_tasks_for_user(user, *, include_active_minutes_in_time_spent: bool = False) -> None:
    """
    Evaluate ONLY the current week's WeeklyTaskAssignments for `user`.
    For each assignment, compute 'current' within [week_start..week_end]
    and update status via `assignment.mark_progress`.

    - TIME_SPENT: sums LessonAttendance.duration (minutes) in week.
      If include_active_minutes_in_time_spent=True and EngagementPing exists,
      adds active ping minutes as well.
    - LESSON: counts attended lessons in week (attended=True).
    - ARTICLE: counts PUBLISHED articles authored this week.
    - WORKSHEET: counts worksheet submissions this week.
    - QUIZ: counts quiz results submitted this week.
    - STREAK: counts distinct active days this week.
    """
    week_start, week_end = current_week_bounds()

    assignments = (
        WeeklyTaskAssignment.objects
        .select_related("task")
        .filter(user=user, week_start=week_start)
    )

    if not assignments.exists():
        return  # Nothing to do this week

    # Pre-aggregate lesson minutes & counts once, to avoid re-querying
    lesson_minutes = (
        LessonAttendance.objects
        .filter(user=user, timestamp__date__gte=week_start, timestamp__date__lte=week_end)
        .aggregate(total=Sum("duration"))
        .get("total") or 0
    )
    attended_count = (
        LessonAttendance.objects
        .filter(user=user, attended=True, timestamp__date__gte=week_start, timestamp__date__lte=week_end)
        .values("lesson_id")
        .distinct()
        .count()
    )

    # Optional aggregates
    article_count = 0
    if DashboardArticle:
        article_count = (
            DashboardArticle.objects
            .filter(author=user, status="PUBLISHED", created_at__date__gte=week_start, created_at__date__lte=week_end)
            .count()
        )

    worksheet_count = 0
    if WorksheetSubmission:
        worksheet_count = (
            WorksheetSubmission.objects
            .filter(user=user, submitted_at__date__gte=week_start, submitted_at__date__lte=week_end)
            .count()
        )

    quiz_count = 0
    if LessonQuizResult:
        # Count any submitted quiz (pass/fail) this week
        # Adjust field name if your model uses a different timestamp.
        field = "submitted_at"
        quiz_count = (
            LessonQuizResult.objects
            .filter(user=user, **_daterange_qs_bounds(week_start, week_end, field))
            .count()
        )

    # Streak (distinct active days)
    streak_days = _distinct_active_days(user, week_start, week_end)

    # Active minutes (from pings) if requested
    ping_minutes = _active_minutes(user, week_start, week_end) if include_active_minutes_in_time_spent else 0

    for assignment in assignments:
        t = assignment.task
        current_value = 0
        progress = {"target": assignment.target}

        if t.task_type == WeeklyTask.TaskType.TIME_SPENT:
            current_value = int(lesson_minutes + ping_minutes)
            # Provide both breakdown and total minutes for UI
            progress.update({
                "minutes": current_value,
                "lesson_minutes": int(lesson_minutes),
                **({"active_minutes": int(ping_minutes)} if include_active_minutes_in_time_spent else {})
            })

        elif t.task_type == WeeklyTask.TaskType.LESSON:
            current_value = int(attended_count)
            progress.update({"count": current_value})

        elif t.task_type == WeeklyTask.TaskType.ARTICLE and DashboardArticle:
            current_value = int(article_count)
            progress.update({"count": current_value})

        elif t.task_type == WeeklyTask.TaskType.WORKSHEET and WorksheetSubmission:
            current_value = int(worksheet_count)
            progress.update({"count": current_value})

        elif t.task_type == WeeklyTask.TaskType.QUIZ and LessonQuizResult:
            current_value = int(quiz_count)
            progress.update({"count": current_value})

        elif t.task_type == WeeklyTask.TaskType.STREAK:
            current_value = int(streak_days)
            progress.update({"days": current_value})

        else:
            # Unknown or disabled integration → leave as is (PENDING)
            current_value = 0

        assignment.mark_progress(current_value, progress_payload=progress)
