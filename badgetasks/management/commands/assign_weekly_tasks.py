# badgetasks/management/commands/assign_weekly_tasks.py
from __future__ import annotations

import random
from typing import Iterable, List, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.timezone import now

from badgetasks.models import WeeklyTask, WeeklyTaskAssignment
from badgetasks.utils import (
    current_week_bounds,
    cooldown_active,
    target_from_task,
    classify_segment,  # optional use
)
from classes.models import LessonAttendance  # for simple segmenting via learning minutes

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Assign weekly tasks (Mon–Sun) to users, enforcing cooldown and audience rules.\n"
        "By default assigns up to 3 tasks per eligible user."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=3,
            help="Max number of tasks to assign per user (default: 3).",
        )
        parser.add_argument(
            "--role",
            type=str,
            choices=[c[0] for c in User.Roles.choices],
            default=None,
            help="Restrict to a specific user role (e.g., FREE).",
        )
        parser.add_argument(
            "--randomize",
            action="store_true",
            help="Randomize task selection order (after filtering).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Ignore cooldown when assigning tasks.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be assigned, without writing to DB.",
        )
        parser.add_argument(
            "--email",
            type=str,
            default=None,
            help="Assign tasks for a single user (by email).",
        )

    def handle(self, *args, **opts):
        week_start, week_end = current_week_bounds()
        limit: int = opts["limit"]
        role_filter = opts["role"]
        randomize: bool = opts["randomize"]
        force: bool = opts["force"]
        dry_run: bool = opts["dry_run"]
        email: str | None = opts["email"]

        self.stdout.write(
            self.style.NOTICE(
                f"Assigning weekly tasks for window {week_start} .. {week_end} "
                f"(limit={limit}, randomize={randomize}, force={force}, dry_run={dry_run})"
            )
        )

        users_qs = User.objects.filter(is_active=True)
        if email:
            users_qs = users_qs.filter(email=email)
        if role_filter:
            users_qs = users_qs.filter(role=role_filter)

        users = list(users_qs)
        if not users:
            raise CommandError("No users match the provided filter(s).")

        # Preload active tasks
        tasks = list(WeeklyTask.objects.filter(is_active=True).order_by("code"))
        if not tasks:
            raise CommandError("No active WeeklyTask rows found. Seed tasks first.")

        total_created = 0
        total_skipped_existing = 0
        total_skipped_cooldown = 0

        for user in users:
            # Filter tasks by audience vs user role
            eligible = [
                t for t in tasks
                if t.audience in (WeeklyTask.Audience.BOTH, user.role)
            ]

            # Optional segment gate (lightweight): compute simple learning minutes
            # for current week + lifetime, then map to NEWBIE / RAMPING / ENGAGED.
            weekly_minutes = (
                LessonAttendance.objects.filter(
                    user=user,
                    timestamp__date__gte=week_start,
                    timestamp__date__lte=week_end,
                )
                .values_list("duration", flat=True)
            )
            weekly_total = sum([m or 0 for m in weekly_minutes])

            lifetime_minutes = (
                LessonAttendance.objects.filter(user=user)
                .values_list("duration", flat=True)
            )
            lifetime_total = sum([m or 0 for m in lifetime_minutes])

            segment = classify_segment(lifetime_total, weekly_total)  # NEWBIE/RAMPING/ENGAGED

            # If a task has min_segment set, ensure user meets it
            def segment_ok(t: WeeklyTask) -> bool:
                if not t.min_segment:
                    return True
                order = ["NEWBIE", "RAMPING", "ENGAGED"]
                return order.index(segment) >= order.index(t.min_segment)

            eligible = [t for t in eligible if segment_ok(t)]

            # Remove tasks already assigned this week
            already_assigned_codes = set(
                WeeklyTaskAssignment.objects.filter(
                    user=user, week_start=week_start
                ).values_list("task__code", flat=True)
            )
            eligible = [t for t in eligible if t.code not in already_assigned_codes]

            # Enforce cooldown
            filtered = []
            for t in eligible:
                if force:
                    filtered.append(t)
                    continue
                if cooldown_active(user, t.code, week_start, t.cooldown_weeks):
                    total_skipped_cooldown += 1
                else:
                    filtered.append(t)
            eligible = filtered

            if not eligible:
                continue

            # Choose order
            if randomize:
                random.shuffle(eligible)
            # Otherwise deterministic by code (already ordered)

            # Limit to N
            chosen = eligible[: max(0, limit)]

            # Create assignments
            for task in chosen:
                target = target_from_task(task)
                if dry_run:
                    self.stdout.write(
                        f"[DRY] Would assign {task.code} to {user.email} "
                        f"(target={target}, week={week_start}..{week_end})"
                    )
                    continue

                with transaction.atomic():
                    obj, created = WeeklyTaskAssignment.objects.get_or_create(
                        user=user,
                        task=task,
                        week_start=week_start,
                        defaults={
                            "week_end": week_end,
                            "target": target,
                            "current": 0,
                            "status": WeeklyTaskAssignment.Status.PENDING,
                            "progress": {"target": target},
                        },
                    )
                    if created:
                        total_created += 1
                    else:
                        total_skipped_existing += 1

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run complete (no DB writes)."))
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created={total_created}, Skipped-existing={total_skipped_existing}, "
                f"Skipped-cooldown={total_skipped_cooldown}"
            )
        )
