import pytest
from django.utils import timezone
from datetime import timedelta
from model_bakery import baker

@pytest.mark.django_db
def test_evaluator_marks_article_completed(free_user, assignments, recent_time):
    # A published dashboard article in the last week -> ARTICLE COMPLETE
    baker.make(
        "dashboard.DashboardArticle",
        author=free_user,
        status="PUBLISHED",
        created_at=recent_time,
        title="My First Post",
        content="...",
    )

    from badgetasks.services.evaluator import evaluate_weekly_tasks_for_user
    from badgetasks.models import WeeklyTaskAssignment

    evaluate_weekly_tasks_for_user(free_user)

    a = WeeklyTaskAssignment.objects.get(user=free_user, task__task_type="ARTICLE")
    assert a.status == "COMPLETED"
    assert a.progress.get("published", 0) >= 1


@pytest.mark.django_db
def test_evaluator_marks_lesson_attendance_completed(free_user, assignments, recent_time):
    # One attended lesson in the last week -> LESSON COMPLETE
    lesson = baker.make("classes.Lesson", date=recent_time)
    baker.make(
        "classes.LessonAttendance",
        user=free_user,
        lesson=lesson,
        attended=True,
        attended_live=True,
        watched_percent=0,
        duration=30,
        timestamp=recent_time,
    )

    from badgetasks.services.evaluator import evaluate_weekly_tasks_for_user
    from badgetasks.models import WeeklyTaskAssignment

    evaluate_weekly_tasks_for_user(free_user)

    a = WeeklyTaskAssignment.objects.get(user=free_user, task__task_type="LESSON")
    assert a.status == "COMPLETED"
    assert a.progress.get("attended") == 1


@pytest.mark.django_db
def test_evaluator_time_spent_in_progress(free_user, assignments, recent_time):
    # 120 minutes only -> IN_PROGRESS for required 5 hours
    lesson = baker.make("classes.Lesson", date=recent_time)
    baker.make(
        "classes.LessonAttendance",
        user=free_user,
        lesson=lesson,
        attended=True,
        duration=120,
        timestamp=recent_time,
    )

    from badgetasks.services.evaluator import evaluate_weekly_tasks_for_user
    from badgetasks.models import WeeklyTaskAssignment

    evaluate_weekly_tasks_for_user(free_user)
    a = WeeklyTaskAssignment.objects.get(user=free_user, task__task_type="TIME_SPENT")
    assert a.status == "IN_PROGRESS"
    assert 1.9 < a.progress.get("hours", 0) < 2.1  # ~2 hours


@pytest.mark.django_db
def test_evaluator_time_spent_completed(free_user, assignments):
    # 5h+ total within last week -> COMPLETED
    now = timezone.now()
    for _ in range(3):
        lesson = baker.make("classes.Lesson", date=now)
        baker.make(
            "classes.LessonAttendance",
            user=free_user,
            lesson=lesson,
            attended=True,
            duration=120,   # 2 hours each
            timestamp=now - timedelta(days=1),
        )

    from badgetasks.services.evaluator import evaluate_weekly_tasks_for_user
    from badgetasks.models import WeeklyTaskAssignment

    evaluate_weekly_tasks_for_user(free_user)
    a = WeeklyTaskAssignment.objects.get(user=free_user, task__task_type="TIME_SPENT")
    assert a.status == "COMPLETED"
    assert a.progress.get("hours", 0) >= 5


@pytest.mark.django_db
def test_evaluator_marks_worksheet_completed(free_user, assignments, recent_time):
    baker.make(
        "worksheet.WorksheetSubmission",
        user=free_user,
        submitted_at=recent_time
    )

    from badgetasks.services.evaluator import evaluate_weekly_tasks_for_user
    from badgetasks.models import WeeklyTaskAssignment

    evaluate_weekly_tasks_for_user(free_user)
    a = WeeklyTaskAssignment.objects.get(user=free_user, task__task_type="WORKSHEET")
    assert a.status == "COMPLETED"
    assert a.progress.get("submitted") == 1


@pytest.mark.django_db
def test_evaluator_leaves_pending_when_no_activity(free_user, assignments):
    from badgetasks.services.evaluator import evaluate_weekly_tasks_for_user
    from badgetasks.models import WeeklyTaskAssignment

    evaluate_weekly_tasks_for_user(free_user)
    for a in WeeklyTaskAssignment.objects.filter(user=free_user):
        if a.task.task_type in {"ARTICLE", "LESSON", "WORKSHEET"}:
            assert a.status == "PENDING"
        elif a.task.task_type == "TIME_SPENT":
            assert a.status == "PENDING"
            assert a.progress.get("hours", 0) == 0
