from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import User
from badgetasks.models import WeeklyTask, WeeklyTaskAssignment

@receiver(post_save, sender=User)
def assign_weekly_tasks_on_user_creation(sender, instance, created, **kwargs):
    if not created or instance.role != User.Roles.FREE:
        return

    # Get active default tasks
    tasks = WeeklyTask.objects.filter(is_active=True)

    for task in tasks:
        WeeklyTaskAssignment.objects.get_or_create(user=instance, task=task)
