# badgetasks/management/commands/assign_weekly_tasks.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from badgetasks.models import WeeklyTaskAssignment, WeeklyTask


User = get_user_model()

class Command(BaseCommand):
    help = "Assign active weekly tasks to all FREE users."

    def handle(self, *args, **options):
        tasks = WeeklyTask.objects.filter(is_active=True)
        users = User.objects.filter(role=User.Roles.FREE, is_active=True)
        new_count = 0
        for user in users:
            for task in tasks:
                _, created = WeeklyTaskAssignment.objects.get_or_create(user=user, task=task)
                if created:
                    new_count += 1
        self.stdout.write(self.style.SUCCESS(
            f"Weekly tasks assigned. Total new assignments: {new_count}"
        ))
