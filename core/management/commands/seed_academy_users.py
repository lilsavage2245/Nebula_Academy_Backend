# core/management/commands/seed_academy_users.py
import sys
import json
import pathlib
from typing import Dict, Any, List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from django.apps import apps

try:
    import yaml  # optional, but recommended
    YAML_AVAILABLE = True
except Exception:
    YAML_AVAILABLE = False

User = get_user_model()


def load_yaml(path: pathlib.Path) -> Dict[str, Any]:
    if not YAML_AVAILABLE:
        raise CommandError("PyYAML is not installed. Install with `pip install pyyaml` or pass --sample.")
    if not path.exists():
        raise CommandError(f"YAML config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


from django.core.exceptions import MultipleObjectsReturned

def get_program_level(ref: dict = None, slug: str = None):
    """
    Resolve ProgramLevel by either:
      - slug (if your model has it), OR
      - ref dict with any of:
          { "category": "BEG", "level_number": 1 }
          { "name": "Beginner Program", "level_number": 1 }
          { "category": "BEG", "level_number": 1, "title": "Core Foundations" }
    """
    ProgramLevel = apps.get_model("program", "ProgramLevel")

    # 1) Try slug ONLY if model actually has it
    if slug and hasattr(ProgramLevel, "_meta") and any(f.name == "slug" for f in ProgramLevel._meta.get_fields()):
        try:
            return ProgramLevel.objects.select_related("program").get(slug=slug)
        except ProgramLevel.DoesNotExist:
            return None

    if not ref:
        return None

    q = {}
    if "category" in ref:      # program category code: PRE/BEG/INT/ADV
        q["program__category"] = ref["category"]
    if "name" in ref:          # program name
        q["program__name"] = ref["name"]
    if "level_number" in ref:
        q["level_number"] = ref["level_number"]
    if "title" in ref:         # level title (optional)
        q["title"] = ref["title"]

    try:
        return ProgramLevel.objects.select_related("program").get(**q)
    except ProgramLevel.DoesNotExist:
        return None
    except MultipleObjectsReturned:
        # If ambiguous, require the caller to specify more fields (e.g., add title)
        return None



def derive_program_category_code_from_level(level) -> Optional[str]:
    """
    Expect ProgramLevel has a FK 'program' with a 'category' or similar code
    (e.g., 'PRE', 'BEG', 'INT', 'ADV'). If your field name is different,
    adjust here.
    """
    # Common patterns: program.category or program.program_category
    if hasattr(level.program, "category"):
        return level.program.category
    if hasattr(level.program, "program_category"):
        return level.program.program_category
    return None


DEFAULT_SAMPLE = {
    # Superuser/admin (at least one)
    "admins": [
        {
            "email": "admin@nebulacodeacademy.com",
            "first_name": "Nebula",
            "last_name": "Admin",
            "password": "AdminPass123!",
        }
    ],
    # Staff-like roles
    "lecturers": [
        {
            "email": "oluchi.okoye@lecturer.nebulacodeacademy.com",
            "first_name": "Oluchi",
            "last_name": "Okoye",
            "password": "Lecturer123!",
            "location": "Leeds, United Kingdom",
        }
    ],
    "volunteers": [
        {
            "email": "volunteer1@nebulacodeacademy.com",
            "first_name": "Ada",
            "last_name": "Eze",
            "password": "Volunteer123!",
        }
    ],
    "partners": [
        {
            "email": "partner@nebulacodeacademy.com",
            "first_name": "Partner",
            "last_name": "Org",
            "password": "Partner123!",
        }
    ],
    "bloggers": [
        {
            "email": "blogger@nebulacodeacademy.com",
            "first_name": "Bola",
            "last_name": "Writes",
            "password": "Blogger123!",
        }
    ],
    # Students
    "free_students": [
        # FREE users require program_category (PRE/BEG/INT/ADV)
        {
            "email": "free.beg1@example.com",
            "first_name": "Ebele",
            "last_name": "Jonathan",
            "password": "FreeStudent123!",
            "program_category": "BEG",
            "location": "Leeds, United Kingdom",
        },
        {
            "email": "free.pre1@example.com",
            "first_name": "Chika",
            "last_name": "Okafor",
            "password": "FreeStudent123!",
            "program_category": "PRE",
        },
    ],
    "enrolled_students": [
        # ENROLLED users require valid program_level slug
        # Replace with your real ProgramLevel slugs (e.g., 'beginner-level-1-core-foundations')
        {
            "email": "enrolled.beg1@example.com",
            "first_name": "Sam",
            "last_name": "Learner",
            "password": "Enrolled123!",
            "program_level_slug": "beginner-level-1-core-foundations",
        }
    ],
    # Global defaults applied to all created/updated users unless overridden
    "defaults": {
        "is_active": True,
        "school_email_verified": False,
        "mfa_enabled": False,
        "theme_preference": None,
        "personalised_class_filter": None,
        "location": None,
    },
}
    

class Command(BaseCommand):
    help = "Seed Academy USERS only (admin, staff, students) in an idempotent way."

    def add_arguments(self, parser):
        parser.add_argument(
            "--config",
            type=str,
            help="Path to YAML file describing users to seed.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview actions without writing to the database."
        )

        parser.add_argument(
            "--sample",
            action="store_true",
            help="Seed with built-in sample dataset (safe to run multiple times).",
        )
        parser.add_argument(
            "--activate-all",
            action="store_true",
            help="Force is_active=True for all created/updated users.",
        )

    def _seed_users(self, data, activate_all=False):
        """
        Runs the actual upsert loops. Returns (created, updated, skipped).
        Expects self._upsert_user(), and module-level helpers:
        - get_program_level_by_slug
        - derive_program_category_code_from_level
        """
        created = updated = skipped = 0

        # Ensure buckets present
        buckets = [
            "admins", "lecturers", "volunteers", "partners",
            "bloggers", "free_students", "enrolled_students",
        ]
        for b in buckets:
            data.setdefault(b, [])
        defaults = data.get("defaults", {})

        # Admins / superusers
        for row in data["admins"]:
            c, u = self._upsert_user(
                row, role="ADMIN", superuser=True, staff=True,
                defaults=defaults, activate_all=activate_all
            )
            created += c; updated += u

        # Lecturers
        for row in data["lecturers"]:
            c, u = self._upsert_user(
                row, role="LECTURER", superuser=False, staff=True,
                defaults=defaults, activate_all=activate_all
            )
            created += c; updated += u

        # Volunteers
        for row in data["volunteers"]:
            c, u = self._upsert_user(
                row, role="VOLUNTEER", superuser=False, staff=False,
                defaults=defaults, activate_all=activate_all
            )
            created += c; updated += u

        # Partners
        for row in data["partners"]:
            c, u = self._upsert_user(
                row, role="PARTNER", superuser=False, staff=False,
                defaults=defaults, activate_all=activate_all
            )
            created += c; updated += u

        # Bloggers
        for row in data["bloggers"]:
            c, u = self._upsert_user(
                row, role="BLOGGER", superuser=False, staff=False,
                defaults=defaults, activate_all=activate_all
            )
            created += c; updated += u

        # FREE students (must have program_category)
        for row in data["free_students"]:
            if not row.get("program_category"):
                self.stdout.write(self.style.WARNING(
                    f"Skipping FREE user without program_category: {row.get('email')}"
                ))
                skipped += 1
                continue
            c, u = self._upsert_user(
                row, role="FREE", superuser=False, staff=False,
                defaults=defaults, activate_all=activate_all
            )
            created += c; updated += u

        # ENROLLED students (must have program_level_slug)
        for row in data["enrolled_students"]:
            level_ref = row.get("program_level_ref")  # dict like {"category":"BEG","level_number":1}
            level_slug = row.get("program_level_slug")  # still supported if you later add slug

            level = get_program_level(ref=level_ref, slug=level_slug)
            if not level:
                self.stdout.write(self.style.WARNING(
                    "Skipping ENROLLED user; ProgramLevel not found for "
                    f"ref={level_ref or level_slug!r} (email={row.get('email')})"
                ))
                skipped += 1
                continue


            # Mirror program category from the level's program if available
            row["program_level"] = level
            cat = derive_program_category_code_from_level(level)
            if cat:
                row["program_category"] = cat

            c, u = self._upsert_user(
                row, role="ENROLLED", superuser=False, staff=False,
                defaults=defaults, activate_all=activate_all
            )
            created += c; updated += u

        return created, updated, skipped


    def handle(self, *args, **options):
        from django.db import transaction

        config_path  = options.get("config")
        use_sample   = options.get("sample")
        activate_all = options.get("activate_all")
        dry_run      = options.get("dry_run")

        if not config_path and not use_sample:
            raise CommandError("Provide --config path to YAML or use --sample.")

        data = DEFAULT_SAMPLE if use_sample else load_yaml(pathlib.Path(config_path))

        # Normalize top-level keys and defaults (also done in _seed_users, but harmless here)
        for b in ["admins","lecturers","volunteers","partners","bloggers","free_students","enrolled_students"]:
            data.setdefault(b, [])
        data.setdefault("defaults", {})

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "Running in DRY-RUN mode: no database writes will be committed."
            ))
            try:
                with transaction.atomic():
                    created, updated, skipped = self._seed_users(data, activate_all=activate_all)
                    self.stdout.write(self.style.SUCCESS(
                        f"[DRY-RUN] Would have created={created}, updated={updated}, skipped={skipped}"
                    ))
                    # Force rollback by raising an exception we immediately swallow
                    raise transaction.TransactionManagementError("Dry run complete; rolling back changes.")
            except transaction.TransactionManagementError:
                # Swallow the forced rollback—this is expected in dry-run
                self.stdout.write(self.style.WARNING("Dry-run completed and rolled back."))
        else:
            created, updated, skipped = self._seed_users(data, activate_all=activate_all)
            self.stdout.write(self.style.SUCCESS(
                f"User seeding complete. created={created}, updated={updated}, skipped={skipped}"
            ))

    # ---------------------
    # Helpers
    # ---------------------

    def _upsert_user(
        self,
        row: Dict[str, Any],
        role: str,
        superuser: bool,
        staff: bool,
        defaults: Dict[str, Any],
        activate_all: bool,
    ):
        """
        Create or update a user by email. Idempotent.
        """
        email = row["email"].lower().strip()
        first_name = row.get("first_name", "").strip() or "User"
        last_name  = row.get("last_name", "").strip() or "Account"
        password   = row.get("password", "ChangeMe123!")

        # Apply global defaults safely (only if not set)
        payload = {**defaults, **row}
        for k in ("is_active", "school_email_verified", "mfa_enabled",
                  "theme_preference", "personalised_class_filter", "location"):
            payload[k] = payload.get(k, defaults.get(k))

        # Enforce flags
        if activate_all:
            payload["is_active"] = True

        # Remove fields that shouldn't be passed to create/update directly
        program_level_obj = payload.pop("program_level", None)
        program_level_slug = payload.pop("program_level_slug", None)  # consumed earlier
        payload.pop("password", None)  # set via set_password
        # Allowed scalar fields we’ll update
        scalar_fields = {
            "first_name", "last_name", "role", "is_active", "is_staff", "is_superuser",
            "school_email_verified", "mfa_enabled", "social_auth_provider",
            "is_deleted", "deleted_at", "location", "theme_preference",
            "personalised_class_filter", "program_category"
        }

        # Upsert
        created = updated = 0
        try:
            user = User.objects.get(email=email)
            # Update existing
            for k, v in payload.items():
                if k in scalar_fields:
                    setattr(user, k, v)
            user.role = role
            user.is_staff = staff or user.is_staff
            user.is_superuser = superuser or user.is_superuser
            if program_level_obj:
                user.program_level = program_level_obj
            # Only reset password if explicitly provided in row
            if "password" in row:
                user.set_password(password)
                user.password_changed_at = timezone.now()
            user.save(update_fields=None)
            updated = 1
            action = "Updated"
        except User.DoesNotExist:
            # Create new
            extra = {
                "role": role,
                "is_staff": staff,
                "is_superuser": superuser,
                "is_active": payload.get("is_active", True),
                "school_email_verified": payload.get("school_email_verified", False),
                "mfa_enabled": payload.get("mfa_enabled", False),
                "social_auth_provider": payload.get("social_auth_provider"),
                "is_deleted": payload.get("is_deleted", False),
                "deleted_at": payload.get("deleted_at"),
                "location": payload.get("location"),
                "theme_preference": payload.get("theme_preference"),
                "personalised_class_filter": payload.get("personalised_class_filter"),
                "program_category": payload.get("program_category"),
            }
            if program_level_obj:
                extra["program_level"] = program_level_obj
                
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                **extra,
            )
            if program_level_obj:
                user.program_level = program_level_obj
                user.save(update_fields=["program_level"])
            created = 1
            action = "Created"

        self.stdout.write(f"{action} {role} user: {email}")
        return created, updated
