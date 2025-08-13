import pytest
from model_bakery import baker

@pytest.mark.django_db
def test_signal_assigns_tasks_to_new_free_user(weekly_tasks):
    # When we create a FREE user, signal should create assignments for all active tasks
    user = baker.make("core.User", role="FREE", email="newfree@example.com", is_active=True)

    from badgetasks.models import WeeklyTaskAssignment
    assignments = WeeklyTaskAssignment.objects.filter(user=user)
    assert assignments.count() == len(weekly_tasks)
