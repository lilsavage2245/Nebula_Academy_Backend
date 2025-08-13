import pytest
from django.core.management import call_command
from model_bakery import baker

@pytest.mark.django_db
def test_assign_weekly_tasks_command_assigns_to_all_free_users(weekly_tasks):
    u1 = baker.make("core.User", role="FREE", is_active=True)
    u2 = baker.make("core.User", role="FREE", is_active=True)
    u3 = baker.make("core.User", role="ENROLLED", is_active=True)  # should be ignored

    call_command("assign_weekly_tasks")

    from badgetasks.models import WeeklyTaskAssignment
    assert WeeklyTaskAssignment.objects.filter(user=u1).count() == len(weekly_tasks)
    assert WeeklyTaskAssignment.objects.filter(user=u2).count() == len(weekly_tasks)
    assert WeeklyTaskAssignment.objects.filter(user=u3).count() == 0
