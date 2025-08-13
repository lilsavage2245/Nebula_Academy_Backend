from datetime import timedelta
from django.utils.timezone import now
from django.db import models
from classes.models import LessonAttendance
from dashboard.models import DashboardArticle
from worksheet.models import WorksheetSubmission
from badgetasks.models import WeeklyTaskAssignment


def evaluate_weekly_tasks_for_user(user):
    """
    Go through each assigned task for the user and update progress & status.
    This runs every time the dashboard is loaded or via a signal/cron.
    """
    one_week_ago = now() - timedelta(days=7)
    assignments = WeeklyTaskAssignment.objects.filter(user=user).select_related('task')

    for assignment in assignments:
        task = assignment.task
        progress = {}

        # Task Type Evaluation
        if task.task_type == "ARTICLE":
            count = DashboardArticle.objects.filter(
                author=user,
                status="PUBLISHED",
                created_at__gte=one_week_ago
            ).count()
            assignment.status = "COMPLETED" if count >= 1 else "PENDING"
            progress["published"] = count

        elif task.task_type == "LESSON":
            attended = LessonAttendance.objects.filter(
                user=user,
                attended=True,
                timestamp__gte=one_week_ago
            ).exists()
            assignment.status = "COMPLETED" if attended else "PENDING"
            progress["attended"] = 1 if attended else 0

        elif task.task_type == "TIME_SPENT":
            total_minutes = LessonAttendance.objects.filter(
                user=user,
                timestamp__gte=one_week_ago
            ).aggregate(total=models.Sum("duration"))["total"] or 0
            hours = total_minutes / 60
            progress["hours"] = round(hours, 2)

            if hours >= task.required_hours:
                assignment.status = "COMPLETED"
            elif hours > 0:
                assignment.status = "IN_PROGRESS"
            else:
                assignment.status = "PENDING"

        elif task.task_type == "WORKSHEET":
            submitted = WorksheetSubmission.objects.filter(
                user=user,
                submitted_at__gte=one_week_ago
            ).exists()
            assignment.status = "COMPLETED" if submitted else "PENDING"
            progress["submitted"] = 1 if submitted else 0

        # Save results
        assignment.progress = progress
        assignment.save(update_fields=["status", "progress", "updated_at"])
