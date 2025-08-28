from celery import shared_task
from django.core.management import call_command

@shared_task
def assign_weekly_tasks_job():
    """
    Runs the management command to assign tasks to FREE users.
    Adjust args if you want randomness or different roles.
    """
    call_command("assign_weekly_tasks", role="FREE", limit=3, randomize=True)
