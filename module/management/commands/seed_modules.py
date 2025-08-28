# module/management/commands/seed_modules.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from pathlib import Path
from typing import Dict, Any, List

import yaml

from module.models import (
    Module, ModuleLevelLink, ModuleLecturer,
    ModuleMaterial, MaterialType, MaterialAudience,
    EvaluationComponent
)
from program.models import ProgramLevel

User = get_user_model()


def _log(stdout, msg: str, dry: bool) -> None:
    stdout.write(f"{'[DRY] ' if dry else ''}{msg}")


def _resolve_levels(levels_cfg):
    """
    Supports either:
      levels: [ "beginner-level-1" ]           # list of slugs
    or:
      levels:
        slugs: ["beginner-level-1"]
        ids: [3, 5]
        title_hints: ["Beginner", "Level 1"]
    """
    if not levels_cfg:
        return []

    resolved = []
    if isinstance(levels_cfg, list):
        resolved += list(ProgramLevel.objects.filter(slug__in=levels_cfg))
    else:
        slugs = levels_cfg.get("slugs") or []
        ids = levels_cfg.get("ids") or []
        hints = levels_cfg.get("title_hints") or []

        if slugs:
            resolved += list(ProgramLevel.objects.filter(slug__in=slugs))
        if ids:
            resolved += list(ProgramLevel.objects.filter(id__in=ids))
        if hints:
            qs = ProgramLevel.objects.all()
            for h in hints:
                qs = qs.filter(title__icontains=h)
            resolved += list(qs)

    # de-dupe
    seen = set()
    unique = []
    for lvl in resolved:
        if lvl.pk not in seen:
            seen.add(lvl.pk)
            unique.append(lvl)
    return unique


def _get_or_create_lecturer(email_raw):
    """Normalize email and ensure a lecturer exists."""
    email = (email_raw or "").strip().lower()
    if not email:
        return None, False
    user, created = User.objects.get_or_create(
        email=email,
        defaults={"role": "LECTURER", "is_active": True},
    )
    return user, created


class Command(BaseCommand):
    help = "Seed academy modules from a YAML config file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--config",
            type=str,
            default="seeds/seed_modules.yml",
            help="Path to YAML config file containing modules",
        )
        parser.add_argument(
            "--activate-all",
            action="store_true",
            help="Mark all seeded modules as active",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate seeding without writing to the database",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Recreate materials/evaluations for a module before inserting",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        config_path: str = options["config"]
        activate_all: bool = options["activate_all"]
        dry_run: bool = options["dry_run"]
        force: bool = options["force"]

        path = Path(config_path)
        if not path.exists():
            raise CommandError(f"Config file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = yaml.safe_load(f) or {}

        modules: List[Dict[str, Any]] = data.get("modules", [])
        if not modules:
            _log(self.stdout, "No modules found in config.", dry_run)
            # if dry_run we still rollback, but nothing to do
            if dry_run:
                raise CommandError("Dry run complete (no changes).")
            return

        created, updated = 0, 0

        for module_data in modules:
            c, u = self._create_or_update_module(module_data, activate_all, dry_run, force)
            created += c
            updated += u

        summary = f"Done. Modules created={created}, updated={updated}."
        _log(self.stdout, summary, dry_run)
        if dry_run:
            # ensure nothing was committed
            raise CommandError("Dry run complete (rolled back).")

    def _create_or_update_module(
        self,
        module_data: Dict[str, Any],
        activate_all: bool,
        dry_run: bool,
        force: bool,
    ) -> tuple[int, int]:
        """
        Create or update a Module and its related objects from YAML data.
        Returns (created_count, updated_count) for modules only.
        """
        title: str = module_data["title"].strip()
        description: str = module_data.get("description", "")
        prerequisites: str = module_data.get("prerequisites", "")
        tools: List[str] = module_data.get("tools_software", [])

        # Upsert Module
        defaults = {
            "description": description,
            "prerequisites": prerequisites,
            "tools_software": tools,
            "is_standalone": module_data.get("is_standalone", False),
            "is_active": activate_all or module_data.get("is_active", True),
        }

        module, created = Module.objects.get_or_create(title=title, defaults=defaults)
        if created:
            _log(self.stdout, f"Created module: {module.title}", dry_run)
        else:
            # Update fields
            for k, v in defaults.items():
                setattr(module, k, v)
            if not dry_run:
                module.save()
            _log(self.stdout, f"Updated module: {module.title}", dry_run)

        # Levels
        levels_cfg = module_data.get("levels")
        levels = _resolve_levels(levels_cfg)
        for idx, lvl in enumerate(levels, start=1):
            if not dry_run:
                ModuleLevelLink.objects.get_or_create(module=module, level=lvl, defaults={"order": idx})
            _log(self.stdout, f"  • Link Level: {lvl.title} (order={idx})", dry_run)

        # Lecturers
        for lec in module_data.get("lecturers", []):
            user, created_user = _get_or_create_lecturer(lec.get("email"))
            role = lec.get("role", "")
            if not user:
                _log(self.stdout, "  • Skipped lecturer with empty email", dry_run)
                continue
            if not dry_run:
                ModuleLecturer.objects.get_or_create(module=module, lecturer=user, defaults={"role": role})
            created_label = " (created)" if created_user else ""
            _log(self.stdout, f"  • Ensure Lecturer: {user.email}{created_label} role={role or '-'}", dry_run)

        # Materials
        mats = module_data.get("materials", [])
        if force and not dry_run:
            ModuleMaterial.objects.filter(module=module).delete()
        for mat in mats:
            m_title = mat["title"]
            m_type = (mat.get("type") or "LINK").upper()
            m_audience = (mat.get("audience") or "ENROLLED").upper()
            ext_url = mat.get("external_url")
            version = mat.get("version", "v1")

            # Map to enum choices (fallbacks safe)
            type_choice = MaterialType[m_type] if m_type in MaterialType.names else MaterialType.LINK
            aud_choice = MaterialAudience[m_audience] if m_audience in MaterialAudience.names else MaterialAudience.ENROLLED

            if not dry_run:
                obj = ModuleMaterial(
                    module=module,
                    title=m_title,
                    description=mat.get("description", ""),
                    type=type_choice,
                    audience=aud_choice,
                    external_url=ext_url,
                    version=version,
                    is_active=mat.get("is_active", True),
                )
                # IMPORTANT: don't include slug here — your model will auto-generate a unique slug on save()
                obj.full_clean()
                obj.save()
            _log(self.stdout, f"  • Material: {m_title} [{m_type}/{m_audience}] -> {ext_url or '(file)'}", dry_run)

        # Evaluations
        evals = module_data.get("evaluations", [])
        if force and not dry_run:
            EvaluationComponent.objects.filter(module=module).delete()
        for ev in evals:
            etype = (ev.get("type") or "QUIZ").upper()
            ev_title = ev.get("title", etype.title())
            max_score = int(ev.get("max_score", 100))
            weight = float(ev.get("weight", 1.0))
            criteria = ev.get("criteria", {})

            if not dry_run:
                EvaluationComponent.objects.create(
                    module=module,
                    type=etype,
                    title=ev_title,
                    is_required=ev.get("is_required", True),
                    max_score=max_score,
                    weight=weight,
                    criteria=criteria,
                    deadline=ev.get("deadline"),
                )
            _log(self.stdout, f"  • Evaluation: {etype} — {ev_title} (max={max_score}, weight={weight})", dry_run)

        return (1, 0) if created else (0, 1)
