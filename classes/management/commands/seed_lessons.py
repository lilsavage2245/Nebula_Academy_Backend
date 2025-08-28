# classes/management/commands/seed_lessons.py
import yaml
from pathlib import Path
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from django.db import transaction

from django.contrib.auth import get_user_model
from classes.models import (
    Lesson, LessonMaterial,
    LessonComment, LessonRating, LessonAttendance,
    LessonQuiz, LessonQuizQuestion,
)
from module.models import Module
from program.models import ProgramLevel, Session

User = get_user_model()

DELIVERY_CHOICES = {"LIVE", "REC", "HYBRID"}
AUDIENCE_CHOICES = {"FREE", "ENROLLED", "BOTH", "STAFF", "ALL"}  # adjust to your enum

def _aware(dt_str):
    if not dt_str:
        return None
    dt = parse_datetime(str(dt_str))
    if not dt:
        return None
    return make_aware(dt) if dt.tzinfo is None else dt


class Command(BaseCommand):

    help = "Seed lessons (and nested materials/comments/ratings/attendance/quizzes) from a YAML file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", "-f", default="seeds/lessons.yml",
            help="Path to YAML seed file (default: seeds/lessons.yml)"
        )
        parser.add_argument(
            "--only", nargs="*", default=[],
            help="Limit to sections: lessons materials comments ratings attendance quizzes"
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Validate and print actions without writing to DB."
        )
        parser.add_argument(
            "--reset-materials", action="store_true",
            help="Deactivate existing materials for a lesson before re-seeding materials."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.exists():
            self.stdout.write(self.style.ERROR(f"Seed file not found: {path}"))
            return

        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

        lessons = data.get("lessons", [])
        if not lessons:
            self.stdout.write(self.style.WARNING("No lessons found in YAML."))
            return

        only = set([x.lower() for x in options["only"]])
        dry = options["dry_run"]
        reset_materials = options["reset_materials"]

        for item in lessons:
            self._seed_one_lesson(item, only=only, dry=dry, reset_materials=reset_materials)

        if dry:
            self.stdout.write(self.style.SUCCESS("[DRY RUN] Parsed successfully; no changes made."))
        else:
            self.stdout.write(self.style.SUCCESS("Lessons seeding complete."))

    # ----------------- per-lesson -----------------

    def _filter_model_fields(self, ModelCls, data: dict) -> dict:
        """
        Filter out keys from 'data' that aren't concrete fields on ModelCls.
        Avoids crashes if config includes extra keys.
        """
        field_names = {
            f.name
            for f in ModelCls._meta.get_fields()
            if getattr(f, "concrete", False)
            and not getattr(f, "many_to_many", False)
            and not getattr(f, "one_to_many", False)
        }
        return {k: v for k, v in data.items() if k in field_names and v is not None}


    def _seed_one_lesson(self, cfg: dict, *, only, dry: bool, reset_materials: bool):
        slug = cfg.get("slug")
        if not slug:
            self.stdout.write(self.style.ERROR("Each lesson must have a 'slug'. Skipping."))
            return

        delivery = cfg.get("delivery", "REC")
        audience = cfg.get("audience", "BOTH")

        if delivery not in DELIVERY_CHOICES:
            self.stdout.write(self.style.ERROR(f"[{slug}] Invalid delivery: {delivery}. Allowed: {sorted(DELIVERY_CHOICES)}"))
            return
        if audience not in AUDIENCE_CHOICES:
            self.stdout.write(self.style.ERROR(f"[{slug}] Invalid audience: {audience}. Allowed: {sorted(AUDIENCE_CHOICES)}"))
            return

        # Resolve FKs (warn & continue if missing)
        level = self._resolve_level(cfg.get("program_level_slug"))
        module = self._resolve_module(cfg.get("module_slug"))
        session = self._resolve_session(cfg.get("session_id"))

        creator = None
        if cfg.get("created_by"):
            creator = self._resolve_user(cfg.get("created_by"))
            if not creator and not dry:
                self.stdout.write(self.style.WARNING(f"[{slug}] created_by user not found: {cfg.get('created_by')}"))

        payload = {
            "created_by": creator,
            "title": cfg.get("title"),
            "description": cfg.get("description", ""),
            "date": _aware(cfg.get("date")),
            "delivery": delivery,
            "audience": audience,
            "is_published": bool(cfg.get("is_published", False)),
            "duration_minutes": cfg.get("duration_minutes"),
            "video_embed_url": cfg.get("video_embed_url", ""),
            "worksheet_link": cfg.get("worksheet_link", ""),
            "program_level": level,
            "module": module,
            "is_active": True,
        }

        # ✅ Filter to actual Lesson fields (future-proof)
        filtered = self._filter_model_fields(Lesson, payload)

        if dry:
            self.stdout.write(f"[DRY] Lesson {slug}: create/update")
            self.stdout.write(f"      Fields: {sorted(filtered.keys())}")
            dropped = sorted(set(payload.keys()) - set(filtered.keys()))
            if dropped:
                self.stdout.write(self.style.WARNING(f"      Dropped unknown fields: {dropped}"))

            # --- Dry-run: simulate nested sections without DB writes ---
            if not only or "materials" in only:
                for m in cfg.get("materials", []):
                    title = m.get("title", "<no-title>")
                    if m.get("file_path") and not m.get("url"):
                        self.stdout.write(f"  [DRY] Material (file): {title} <- {m.get('file_path')}")
                    elif m.get("url") and not m.get("file_path"):
                        self.stdout.write(f"  [DRY] Material (url):  {title} -> {m.get('url')}")
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"  ⚠ Skipping material '{title}': provide exactly one of file_path or url"
                        ))

            if not only or "comments" in only:
                for c in cfg.get("comments", []):
                    self.stdout.write(f"  [DRY] Comment by {c.get('user','<missing>')} -> {c.get('content','')[:40]}...")
                    for r1 in c.get("replies", []):
                        self.stdout.write(f"    [DRY] Reply by {r1.get('user','<missing>')} -> {r1.get('content','')[:40]}...")
                        for r2 in r1.get("replies", []):
                            self.stdout.write(f"      [DRY] Reply by {r2.get('user','<missing>')} -> {r2.get('content','')[:40]}...")
            if not only or "ratings" in only:
                for r in cfg.get("ratings", []):
                    self.stdout.write(f"  [DRY] Rating {r.get('score')} by {r.get('user','<missing>')}")
            if not only or "attendance" in only:
                for a in cfg.get("attendance", []):
                    self.stdout.write(f"  [DRY] Attendance by {a.get('user','<missing>')} at {a.get('timestamp','<now>')}")
            if not only or "quizzes" in only:
                for q in cfg.get("quizzes", []):
                    self.stdout.write(f"  [DRY] Quiz: {q.get('title','<no-title>')}")
                    for i, qq in enumerate(q.get("questions", []), start=1):
                        self.stdout.write(f"    [DRY] Q{i}: {qq.get('text','')[:60]}")
            return  # end dry-run

            # --- Real write ---
        lesson, created = Lesson.objects.update_or_create(
            slug=slug,
            defaults=filtered
        )
        self.stdout.write(f"{'CREATED' if created else 'UPDATED'} Lesson: {lesson.slug}")

        # Nested sections (real)
        if not only or "materials" in only:
            self._seed_materials(lesson, cfg.get("materials", []), reset=reset_materials, dry=dry)
        if not only or "comments" in only:
            self._seed_comments_tree(lesson, cfg.get("comments", []), dry=dry)
        if not only or "ratings" in only:
            self._seed_ratings(lesson, cfg.get("ratings", []), dry=dry)
        if not only or "attendance" in only:
            self._seed_attendance(lesson, cfg.get("attendance", []), dry=dry)
        if not only or "quizzes" in only:
            self._seed_quizzes(lesson, cfg.get("quizzes", []), dry=dry)


    # ----------------- resolvers (warn, don't crash) -----------------

    def _resolve_level(self, slug):
        if not slug:
            return None
        obj = ProgramLevel.objects.filter(slug=slug).first()
        if not obj:
            self.stdout.write(self.style.WARNING(f"  ⚠ ProgramLevel not found: {slug}"))
        return obj

    def _resolve_module(self, slug):
        if not slug:
            return None
        obj = Module.objects.filter(slug=slug).first()
        if not obj:
            self.stdout.write(self.style.WARNING(f"  ⚠ Module not found: {slug}"))
        return obj

    def _resolve_session(self, sid):
        if not sid:
            return None
        obj = Session.objects.filter(id=sid).first()
        if not obj:
            self.stdout.write(self.style.WARNING(f"  ⚠ Session not found: {sid}"))
        return obj

    def _resolve_user(self, email):
        if not email:
            return None
        user = User.objects.filter(email=email).first()
        if not user:
            self.stdout.write(self.style.WARNING(f"  ⚠ User not found: {email}"))
        return user

    # ----------------- materials -----------------

    def _seed_materials(self, lesson: Lesson, rows: list, *, reset: bool, dry: bool):
        """
        Seeds LessonMaterial with either a local file upload (file_path) or an external URL.
        Enforces exactly one of {file_path, url}. Keeps idempotency by (lesson, title, version).
        """
        if reset and not dry:
            lesson.materials.update(is_active=False)

        for m in rows:
            title = m.get("title")
            if not title:
                self.stdout.write(self.style.WARNING("  ⚠ Skipping material with no title"))
                continue

            uploaded_by = self._resolve_user(m.get("uploaded_by"))
            material_type = m.get("material_type")
            version = m.get("version", 1)
            audience = m.get("audience", lesson.audience)

            file_path = m.get("file_path")
            url = m.get("url", "")

            # Exactly one of file_path or url
            if bool(file_path) == bool(url):
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ Skipping material '{title}': provide exactly one of file_path or url"
                    )
                )
                continue

            if not material_type:
                # optional: infer from extension if missing
                if file_path:
                    ext = (Path(file_path).suffix or "").lower()
                    material_type = {
                        ".pdf": "PDF",
                        ".doc": "DOC",
                        ".docx": "DOC",
                        ".zip": "ZIP",
                        ".mp4": "VIDEO",
                        ".mov": "VIDEO",
                    }.get(ext, "DOC")
                else:
                    material_type = "LINK"  # when using URL, default to LINK

            # Base defaults (exclude file/url here; we set them after update_or_create)
            defaults = {
                "material_type": material_type,
                "version": version,
                "audience": audience,
                "uploaded_by": uploaded_by,
                "is_active": True,
            }

            if dry:
                if file_path:
                    self.stdout.write(f"  [DRY] Material (file): {title} v{version} <- {file_path}")
                else:
                    self.stdout.write(f"  [DRY] Material (url):  {title} v{version} -> {url}")
                continue

            # Create/update the row first (without file/url so we can set them mutually exclusive)
            obj, created = LessonMaterial.objects.update_or_create(
                lesson=lesson,
                title=title,
                version=version,
                defaults=defaults,
            )

            changed_fields = []

            if file_path:
                # attach local file; clear url
                p = Path(file_path)
                if not p.exists() or not p.is_file():
                    self.stdout.write(self.style.WARNING(f"    ⚠ File not found: {file_path}. Material left unchanged."))
                else:
                    with p.open("rb") as fh:
                        # .save() will write to your configured storage (local/S3/etc.)
                        obj.file.save(p.name, ContentFile(fh.read()), save=False)
                    obj.url = ""
                    changed_fields.extend(["file", "url"])
            else:
                # set URL; clear file
                if obj.file:
                    # delete the old file from storage to avoid orphaned files
                    try:
                        obj.file.delete(save=False)
                    except Exception:
                        pass
                obj.file = None
                obj.url = url
                changed_fields.extend(["file", "url"])

            if changed_fields:
                obj.save(update_fields=changed_fields)

            self.stdout.write(f"  {'+' if created else '~'} Material: {obj.title} v{obj.version} ({'file' if file_path else 'url'})")


    # ----------------- threaded comments (recursive) -----------------

    def _seed_comments_tree(self, lesson: Lesson, nodes: list, *, dry: bool):
        for node in nodes:
            self._seed_comment_node(lesson, node, parent=None, dry=dry)

    def _seed_comment_node(self, lesson: Lesson, node: dict, *, parent: LessonComment | None, dry: bool):
        email = node.get("user")
        content = node.get("content")
        if not email or not content:
            self.stdout.write(self.style.WARNING("  ⚠ Skipping comment missing 'user' or 'content'"))
            return

        user = self._resolve_user(email)
        if not user:
            self.stdout.write(self.style.WARNING(f"  ⚠ Skipping comment; user missing: {email}"))
            return

        if dry:
            self.stdout.write(
                f"  [DRY] Comment by {user.email} on {lesson.slug}"
                + (f" (reply to {parent.id})" if parent else "")
            )
            comment = None
        else:
            # best-effort idempotency: same lesson+user+content (& parent) considered identical
            comment, created = LessonComment.objects.get_or_create(
                lesson=lesson, user=user, content=content, parent=parent
            )
            self.stdout.write(
                f"  {'+' if created else '~'} Comment by {user.email}"
                + (f" (reply to {parent.id})" if parent else "")
            )

        for child in node.get("replies", []):
            self._seed_comment_node(lesson, child, parent=comment, dry=dry)

    # ----------------- ratings -----------------

    def _seed_ratings(self, lesson: Lesson, rows: list, *, dry: bool):
        for r in rows:
            email = r.get("user")
            score = r.get("score")
            if not email or score is None:
                self.stdout.write(self.style.WARNING("  ⚠ Skipping rating missing 'user' or 'score'"))
                continue
            user = self._resolve_user(email)
            if not user:
                self.stdout.write(self.style.WARNING(f"  ⚠ Skipping rating; user missing: {email}"))
                continue

            defaults = {
                "score": score,
                "review": r.get("review", "")
            }
            if dry:
                self.stdout.write(f"  [DRY] Rating {defaults['score']} by {user.email}")
                continue
            LessonRating.objects.update_or_create(lesson=lesson, user=user, defaults=defaults)
            self.stdout.write(f"  ~ Rating by {user.email}")

    # ----------------- attendance -----------------

    def _seed_attendance(self, lesson: Lesson, rows: list, *, dry: bool):
        for a in rows:
            email = a.get("user")
            if not email:
                self.stdout.write(self.style.WARNING("  ⚠ Skipping attendance missing 'user'"))
                continue
            user = self._resolve_user(email)
            if not user:
                self.stdout.write(self.style.WARNING(f"  ⚠ Skipping attendance; user missing: {email}"))
                continue

            defaults = {
                "attended": bool(a.get("attended", True)),
                "timestamp": _aware(a.get("timestamp")) if a.get("timestamp") else None,
            }
            if dry:
                self.stdout.write(f"  [DRY] Attendance by {user.email}")
                continue
            LessonAttendance.objects.update_or_create(lesson=lesson, user=user, defaults=defaults)
            self.stdout.write(f"  ~ Attendance by {user.email}")

    # ----------------- quizzes & questions -----------------

    def _seed_quizzes(self, lesson: Lesson, rows: list, *, dry: bool):
        for q in rows:
            title = q.get("title")
            if not title:
                self.stdout.write(self.style.WARNING("  ⚠ Skipping quiz missing 'title'"))
                continue

            q_defaults = {
                "description": q.get("description", ""),
                "is_active": bool(q.get("is_active", True)),
            }

            if dry:
                self.stdout.write(f"  [DRY] Quiz: {title}")
                quiz = None
            else:
                quiz, created = LessonQuiz.objects.update_or_create(
                    lesson=lesson, title=title, defaults=q_defaults
                )
                self.stdout.write(f"  {'+' if created else '~'} Quiz: {quiz.title}")

            for i, qq in enumerate(q.get("questions", []), start=1):
                text = qq.get("text")
                choices = qq.get("choices")
                correct = qq.get("correct_answer")
                if not text or not choices or correct is None:
                    self.stdout.write(self.style.WARNING(f"    ⚠ Skipping question {i}: missing fields"))
                    continue

                if dry:
                    self.stdout.write(f"    [DRY] Q{i}: {text[:60]}")
                    continue

                obj, created_q = LessonQuizQuestion.objects.update_or_create(
                    quiz=quiz, text=text,
                    defaults={"choices": choices, "correct_answer": correct}
                )
                self.stdout.write(f"    {'+' if created_q else '~'} Q{i}: {obj.text[:60]}")
