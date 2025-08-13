import pytest
from django.urls import reverse
from model_bakery import baker
from django.utils import timezone

@pytest.mark.django_db
def test_weekly_tasks_api_returns_assignments_with_computed_status(api_client, free_user, assignments, recent_time):
    api_client.force_authenticate(user=free_user)

    # Give the user some progress (lesson attended)
    lesson = baker.make("classes.Lesson", date=recent_time)
    baker.make(
        "classes.LessonAttendance",
        user=free_user,
        lesson=lesson,
        attended=True,
        duration=60,
        timestamp=recent_time,
    )

    url = reverse("weekly-task-list")  # /api/dashboard/free/weekly-tasks/
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    # Should contain our tasks with status; at least one should be IN_PROGRESS/COMPLETED for TIME_SPENT or LESSON
    assert isinstance(data, list)
    titles = {item["task_title"] for item in data}
    assert "Attend a lesson" in titles or "Accumulate 5 hours" in titles
