from __future__ import annotations
import os
import yaml
from typing import Any, Dict, List

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from badgetasks.models import WeeklyTask


VALID_TYPES = {c for c, _ in WeeklyTask.TaskType.choices}
VALID_AUDIENCE = {c for c, _ in WeeklyTask.Audience.choices}
VALID_SEGMENTS = {c for c, _ in WeeklyTask.MinSegment.choices}


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate + normalize one row.
    Required: code, title, task_type
    Optional: description, audience, min_segment, target_count, cooldown_weeks, required_hours, is_active
    Notes:
      - TIME_SPENT target_count is minutes (300 = 5h)
      - If TIME_SPENT and target_count missing, derive from required_hours*60
    """
    missing = [k for k in ("code", "title", "task_type") if not row.get(k)]
    if missing:
        raise CommandError(f"Missing required fields {missing} in row: {row}")

    code = str(row["code"]).strip().lower()  # store lowercase slug-like
    task_type = str(row["task_type"]).upper().strip()
    if task_type not in VALID_TYPES:
        raise CommandError(f"Invalid task_type '{task_type}' for code='{code}'. Valid: {sorted(VALID_TYPES)}")

    audience = (row.get("audience") or "BOTH").upper().strip()
    if audience not in VALID_AUDIENCE:
        raise CommandError(f"Invalid audience '{audience}' for code='{code}'. Valid: {sorted(VALID_AUDIENCE)}")

    min_segment = row.get("min_segment")
    if min_segment:
        min_segment = str(min_segment).upper().strip()
        if min_segment not in VALID_SEGMENTS:
            raise CommandError(f"Invalid min_segment '{min_segment}' for code='{code}'. Valid: {sorted(VALID_SEGMENTS)}")
    else:
        min_segment = None

    # Targets
    target_count = row.get("target_count")
    required_hours = row.get("required_hours")  # legacy; convert to minutes if provided
    if target_count is None and required_hours is not None and task_type == "TIME_SPENT":
        target_count = int(required_hours) * 60
    if target_count is None:
        target_count = 1
    target_count = int(target_count)

    cooldown_weeks = int(row.get("cooldown_weeks", 1))
    is_active = bool(row.get("is_active", True))
    description = row.get("description", "")

    return {
        "code": code,
        "title": row["title"],
        "description": description,
        "task_type": task_type,
        "audience": audience,
        "min_segment": min_segment,
        "target_count": target_count,
        "cooldown_weeks": cooldown_weeks,
        "required_hours": int(required_hours) if (required_hours is not None) else 0,  # kept for legacy compat
        "is_active": is_active,
    }


class Command(BaseCommand):
    help = "Seed WeeklyTask catalog from a YAML file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--config",
            type=str,
            required=True,
            help="Path to YAML config file that defines task catalog.",
        )
        parser.add_argument(
            "--activate-all",
            action="store_true",
            help="Force all tasks in the file to be set active=True.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and show plan without writing to DB.",
        )

    def handle(self, *args, **opts):
        path = opts["config"]
        activate_all = opts["activate_all"]
        dry = opts["dry_run"]

        if not os.path.exists(path):
            raise CommandError(f"Config file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        rows: List[dict] = data.get("tasks") or []
        if not rows:
            raise CommandError("No 'tasks' found in YAML.")

        normalized: List[dict] = []
        for row in rows:
            norm = _normalize_row(row)
            if activate_all:
                norm["is_active"] = True
            normalized.append(norm)

        self.stdout.write(self.style.NOTICE(f"Loaded {len(normalized)} tasks from {path}"))

        if dry:
            for n in normalized:
                self.stdout.write(f"[DRY] Would upsert task code={n['code']} type={n['task_type']} target={n['target_count']} active={n['is_active']}")
            self.stdout.write(self.style.WARNING("Dry run: no DB writes"))
            return

        # Upsert by code
        created, updated = 0, 0
        with transaction.atomic():
            for n in normalized:
                obj, was_created = WeeklyTask.objects.update_or_create(
                    code=n["code"],
                    defaults={
                        "title": n["title"],
                        "description": n["description"],
                        "task_type": n["task_type"],
                        "audience": n["audience"],
                        "min_segment": n["min_segment"],
                        "target_count": n["target_count"],
                        "cooldown_weeks": n["cooldown_weeks"],
                        "required_hours": n["required_hours"],
                        "is_active": n["is_active"],
                    },
                )
                created += int(was_created)
                updated += int(not was_created)

        self.stdout.write(self.style.SUCCESS(f"Done. Created={created}, Updated={updated}"))
