from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from badgetasks.services.evaluator import evaluate_weekly_tasks_for_user
from badgetasks.models import WeeklyTaskAssignment
from badgetasks.utils import current_week_bounds

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Evaluate current week's WeeklyTaskAssignments for users.\n"
        "Updates each assignment's current/progress/status."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--role",
            type=str,
            choices=[c[0] for c in User.Roles.choices],
            default=None,
            help="Restrict to a specific user role (e.g., FREE).",
        )
        parser.add_argument(
            "--email",
            type=str,
            default=None,
            help="Evaluate a single user by email.",
        )
        parser.add_argument(
            "--include-active-minutes",
            action="store_true",
            help="For TIME_SPENT tasks, include EngagementPing minutes in addition to lesson minutes.",
        )
        parser.add_argument(
            "--silent",
            action="store_true",
            help="Suppress per-user logs; only print summary.",
        )

    def handle(self, *args, **opts):
        role = opts["role"]
        email = opts["email"]
        include_active = opts["include_active_minutes"]
        silent = opts["silent"]

        week_start, week_end = current_week_bounds()
        self.stdout.write(
            self.style.NOTICE(
                f"Evaluating assignments for week {week_start} .. {week_end} "
                f"(include_active_minutes={include_active})"
            )
        )

        users_qs = User.objects.filter(is_active=True)
        if role:
            users_qs = users_qs.filter(role=role)
        if email:
            users_qs = users_qs.filter(email=email)

        users = list(users_qs)
        if not users:
            raise CommandError("No users match the provided filter(s).")

        total_users = 0
        total_assignments = 0

        for user in users:
            # Skip users with no assignments this week
            if not WeeklyTaskAssignment.objects.filter(user=user, week_start=week_start).exists():
                if not silent:
                    self.stdout.write(f"- {user.email}: no assignments this week, skipping")
                continue

            evaluate_weekly_tasks_for_user(
                user,
                include_active_minutes_in_time_spent=include_active,
            )

            count = WeeklyTaskAssignment.objects.filter(user=user, week_start=week_start).count()
            total_users += 1
            total_assignments += count
            if not silent:
                self.stdout.write(self.style.SUCCESS(f"- {user.email}: evaluated {count} assignments"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Users evaluated: {total_users} | Assignments updated: {total_assignments}"
            )
        )
