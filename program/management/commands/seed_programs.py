# program/management/commands/seed_programs.py
from pathlib import Path
from typing import Any, Dict, List
import yaml

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from program.models import Program, ProgramLevel, ProgramCategory

User = get_user_model()

def _level_slug_for(program, level_number, title):
    prog_slug = program.slug or slugify(program.name)
    base = f"{prog_slug}-level-{level_number}-{slugify(title or '')[:40]}".strip("-")
    slug = base or f"{prog_slug}-level-{level_number}"
    # ensure uniqueness
    i = 1
    from program.models import ProgramLevel
    while ProgramLevel.objects.filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug

class Command(BaseCommand):
    help = "Seed Programs and ProgramLevels from a YAML file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--config", required=True,
            help="Path to YAML config, e.g. seeds/seed_programs.yml",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Parse & validate and show actions, but do not write.",
        )
        parser.add_argument(
            "--update", action="store_true",
            help="Update existing Program/Level title & description from YAML.",
        )
        parser.add_argument(
            "--prune", action="store_true",
            help="Delete ProgramLevels that are not listed for a Program.",
        )
        parser.add_argument(
            "--strict", action="store_true",
            help="Fail if unknown keys are present in YAML items (helps catch typos).",
        )
        parser.add_argument(
            "--append-min-age", action="store_true",
            help="If a level has min_age, prefix it in the description (model has no min_age column).",
        )
        parser.add_argument(
            "--activate-all", action="store_true",
            help="Convenience: implies --update and --append-min-age so a fresh DB is fully ready.",
        )
        parser.add_argument(
            "--refresh-level-slugs",
            action="store_true",
            help="After seeding, recompute/assign slugs for all ProgramLevels missing or out-of-date."
        )

    def handle(self, *args, **opts):
        config_path = Path(opts["config"]).resolve()
        if not config_path.exists():
            raise CommandError(f"Config not found: {config_path}")

        # activate-all implies sensible defaults
        if opts["activate_all"]:
            opts["update"] = True
            opts["append_min_age"] = True

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            raise CommandError(f"Failed to read YAML: {e}")

        # validate & normalize
        try:
            seed_programs = self._parse_and_validate(data, strict=opts["strict"])
        except ValueError as ve:
            raise CommandError(str(ve))

        @transaction.atomic
        def apply():
            valid_codes = {c for c, _ in ProgramCategory.choices}

            for p in seed_programs:
                if p["category"] not in valid_codes:
                    raise CommandError(
                        f"Invalid category '{p['category']}' for program '{p['name']}'. "
                        f"Valid: {sorted(valid_codes)}"
                    )

                # Optional: link director
                director = None
                if p.get("director_email"):
                    director = User.objects.filter(
                        email=p["director_email"], role="LECTURER"
                    ).first()
                    if director is None:
                        self.stdout.write(self.style.WARNING(
                            f"  ! Director '{p['director_email']}' not found as LECTURER. Skipping link."
                        ))

                prog, created = Program.objects.get_or_create(
                    category=p["category"],
                    name=p["name"],
                    defaults={
                        "description": p.get("description", ""),
                        "director": director,
                    },
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"+ Program created: {prog}"))
                else:
                    self.stdout.write(self.style.NOTICE(f"= Program exists: {prog}"))
                    changed = False
                    if opts["update"] and p.get("description") is not None and prog.description != p["description"]:
                        prog.description = p["description"]; changed = True
                    if director and prog.director_id != director.id:
                        prog.director = director; changed = True
                    if changed:
                        prog.save(update_fields=["description", "director"])
                        self.stdout.write(self.style.SUCCESS(f"  • Program updated: {prog}"))

                # Levels
                yaml_levels = {int(lv["level_number"]): lv for lv in p.get("levels", [])}
                existing_qs = ProgramLevel.objects.filter(program=prog)
                existing_map = {lv.level_number: lv for lv in existing_qs}

                for num, lv in sorted(yaml_levels.items()):
                    title = lv.get("title", f"Level {num}")
                    description = lv.get("description", "") or ""

                    # Optional: append min_age note
                    min_age = lv.get("min_age")
                    if opts["append_min_age"] and min_age:
                        prefix = f"Min Age: {min_age} — "
                        if not description.startswith(prefix):
                            description = f"{prefix}{description}".strip()

                    if num in existing_map:
                        lvl = existing_map[num]
                        changed = False
                        if opts["update"] and (lvl.title != title or lvl.description != description):
                            lvl.title = title
                            lvl.description = description
                            changed = True
                        if not lvl.slug:
                            lvl.slug = _level_slug_for(prog, num, title)
                            changed = True
                        if changed:
                            lvl.save(update_fields=["title", "description", "slug"])
                            self.stdout.write(self.style.SUCCESS(
                                f"  • Level {num} updated: {title}"
                            ))
                        else:
                            self.stdout.write(self.style.NOTICE(
                                f"  = Level {num} exists: {lvl.title}"
                            ))
                    else:
                        lvl = ProgramLevel.objects.create(
                            program=prog,
                            level_number=num,
                            title=title,
                            description=description,
                        )
                        if not lvl.slug:
                            lvl.slug = _level_slug_for(prog, num, title)
                            lvl.save(update_fields=["slug"])
                        self.stdout.write(self.style.SUCCESS(
                            f"  + Level {num} created: {title}"
                        ))

                if opts["prune"]:
                    to_delete = [lv for n, lv in existing_map.items() if n not in yaml_levels]
                    for lv in to_delete:
                        self.stdout.write(self.style.WARNING(
                            f"  - Pruning level {lv.level_number}: {lv.title}"
                        ))
                        lv.delete()

        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry-run: no changes will be saved."))
            try:
                apply()
                # rollback the transaction deliberately
                raise RuntimeError("Rollback dry-run")
            except RuntimeError:
                self.stdout.write(self.style.WARNING("Dry-run complete."))
        else:
            apply()
            self.stdout.write(self.style.SUCCESS("Seeding complete."))

    # ---------- helpers ----------

    def _parse_and_validate(self, data: Dict[str, Any], strict: bool) -> List[Dict[str, Any]]:
        if not isinstance(data, dict) or "programs" not in data:
            raise ValueError("YAML must be a mapping containing a top-level 'programs' list.")

        programs = data.get("programs") or []
        if not isinstance(programs, list):
            raise ValueError("'programs' must be a list.")

        allowed_program_keys = {"category", "name", "description", "director_email", "levels"}
        allowed_level_keys = {"level_number", "title", "description", "min_age"}

        cleaned = []
        for i, p in enumerate(programs, start=1):
            if strict:
                unknown = set(p.keys()) - allowed_program_keys
                if unknown:
                    raise ValueError(f"Program #{i} has unknown keys: {sorted(unknown)}")

            if "category" not in p or "name" not in p:
                raise ValueError(f"Program #{i} must include 'category' and 'name'.")

            levels = p.get("levels") or []
            if not isinstance(levels, list):
                raise ValueError(f"Program #{i} 'levels' must be a list.")

            norm_levels = []
            for j, lv in enumerate(levels, start=1):
                if strict:
                    unknown_lv = set(lv.keys()) - allowed_level_keys
                    if unknown_lv:
                        raise ValueError(
                            f"Program '{p['name']}' level #{j} has unknown keys: {sorted(unknown_lv)}"
                        )
                if "level_number" not in lv:
                    raise ValueError(
                        f"Program '{p['name']}' level #{j} must include 'level_number'."
                    )
                try:
                    lv_num = int(lv["level_number"])
                except Exception:
                    raise ValueError(
                        f"Program '{p['name']}' level #{j} 'level_number' must be an integer."
                    )

                norm_levels.append({
                    "level_number": lv_num,
                    "title": lv.get("title", f"Level {lv_num}"),
                    "description": lv.get("description", "") or "",
                    "min_age": lv.get("min_age"),
                })

            cleaned.append({
                "category": p["category"],
                "name": p["name"],
                "description": p.get("description", "") or "",
                "director_email": p.get("director_email"),
                "levels": norm_levels,
            })

        return cleaned

    def _refresh_all_level_slugs(self):
        from program.models import ProgramLevel
        from django.utils.text import slugify

        updated = 0
        for lvl in ProgramLevel.objects.select_related("program").all():
            desired_base = f"{(lvl.program.slug or slugify(lvl.program.name))}-level-{lvl.level_number}-{slugify(lvl.title)[:40]}".strip("-")
            if not lvl.slug or not lvl.slug.startswith(desired_base):
                # compute new unique slug
                i = 1
                slug = desired_base or f"{lvl.program.slug}-level-{lvl.level_number}"
                while ProgramLevel.objects.filter(slug=slug).exclude(pk=lvl.pk).exists():
                    slug = f"{desired_base}-{i}"
                    i += 1
                lvl.slug = slug
                lvl.save(update_fields=["slug"])
                updated += 1
        if updated:
            self.stdout.write(self.style.SUCCESS(f"Refreshed slugs for {updated} ProgramLevels."))
        else:
            self.stdout.write(self.style.NOTICE("All ProgramLevel slugs already up to date."))