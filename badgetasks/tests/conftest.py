import pytest
from django.utils import timezone
from model_bakery import baker
from datetime import timedelta
from rest_framework.test import APIClient

@pytest.fixture
def free_user(db):
    return baker.make(
        "core.User",
        role="FREE",
        first_name="Ebele",
        last_name="Jonathan",
        email="ebele@example.com",
        is_active=True,
    )

@pytest.fixture
def weekly_tasks(db):
    # Active tasks: ARTICLE, LESSON, TIME_SPENT(5h), WORKSHEET
    t1 = baker.make("badgetasks.WeeklyTask", title="Write and publish an article", task_type="ARTICLE", is_active=True)
    t2 = baker.make("badgetasks.WeeklyTask", title="Attend a lesson", task_type="LESSON", is_active=True)
    t3 = baker.make("badgetasks.WeeklyTask", title="Accumulate 5 hours", task_type="TIME_SPENT", required_hours=5, is_active=True)
    t4 = baker.make("badgetasks.WeeklyTask", title="Submit a worksheet", task_type="WORKSHEET", is_active=True)
    return t1, t2, t3, t4

@pytest.fixture
def assignments(db, free_user, weekly_tasks):
    # Normally assigned by signal/command; we create explicitly for isolated tests
    return [
        baker.make("badgetasks.WeeklyTaskAssignment", user=free_user, task=t)
        for t in weekly_tasks
    ]

@pytest.fixture
def recent_time():
    return timezone.now() - timedelta(days=1)

@pytest.fixture
def old_time():
    return timezone.now() - timedelta(days=14)

@pytest.fixture
def api_client():
    return APIClient()