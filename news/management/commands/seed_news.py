# news/management/commands/seed_news.py
import io
import os
import yaml
import urllib.request
from urllib.parse import urlparse
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from news.models import NewsCategory, NewsPost, NewsComment, NewsReaction, NewsSubscriber
from django.utils.dateparse import parse_datetime, parse_date
from datetime import datetime, tzinfo

User = get_user_model()


class Command(BaseCommand):
    help = "Seed news categories, posts, comments, reactions, and subscribers"

    def add_arguments(self, parser):
        parser.add_argument("--config", type=str, help="Path to YAML config file")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be created without saving")
        parser.add_argument("--clear-first", action="store_true", help="Delete existing records before seeding")
        parser.add_argument("--images-dir", type=str, default="", help="Base directory for local images in YAML")
        parser.add_argument("--download-images", action="store_true",
                            help="Allow downloading image_url over HTTP(S) (useful for placeholders)")
        parser.add_argument("--tz", type=str, default=None,
                            help="IANA timezone name to assume for naive datetimes (defaults to settings.TIME_ZONE)")
    
    # --- helpers ---
    def _aware_dt(self, raw, tz=None):
        """
        Parse 'raw' into a timezone-aware datetime.
        Accepts:
        - ISO 8601: '2025-08-18T10:30:00', '2025-08-18T10:30:00Z', '2025-08-18T10:30:00+01:00'
        - 'YYYY-MM-DD HH:MM:SS'
        - 'YYYY-MM-DD' (interpreted as midnight)
        Behavior:
        - If naive, make aware using tz (or current timezone).
        - If aware and tz is provided, convert to tz.
        """
        if not raw:
            return None

        # First try datetime parse
        dt = parse_datetime(str(raw))

        # If that failed, try date-only and set midnight
        if dt is None:
            d = parse_date(str(raw))
            if d:
                dt = datetime(d.year, d.month, d.day, 0, 0, 0)

        if dt is None:
            return None

        # Make or convert to target timezone
        target_tz = tz or timezone.get_current_timezone()

        if timezone.is_naive(dt):
            return timezone.make_aware(dt, target_tz)

        # Already aware: convert if a specific tz was requested
        try:
            return dt.astimezone(target_tz) if tz else dt
        except Exception:
            # Fallback: return as-is if conversion fails for some reason
            return dt


    # ---------- image helpers ----------
    def _read_local_image(self, base_dir, path_or_rel):
        """
        Returns (filename, ContentFile) for a local image path; None if not found.
        """
        # If absolute, use as-is; else resolve relative to base_dir
        img_path = path_or_rel if os.path.isabs(path_or_rel) else os.path.join(base_dir or "", path_or_rel)
        if not os.path.exists(img_path):
            return None
        with open(img_path, "rb") as f:
            data = f.read()
        filename = os.path.basename(img_path)
        return filename, ContentFile(data)

    def _download_image(self, url):
        """
        Returns (filename, ContentFile) from remote URL; None if fails.
        """
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = resp.read()
            # best-effort filename from URL
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path) or "downloaded.jpg"
            return filename, ContentFile(data)
        except Exception as e:
            self.stderr.write(self.style.WARNING(f"Could not download image: {url} ({e})"))
            return None

    def _attach_image(self, post, image_field_name, filename, content_file):
        # Ensure upload_to path on model handles unique names
        getattr(post, image_field_name).save(filename, content_file, save=False)

    def handle(self, *args, **options):
        config_path = options["config"]
        dry_run = options["dry_run"]
        clear_first = options["clear_first"]
        images_dir = options["images_dir"]
        allow_download = options["download_images"]

        if not config_path:
            self.stderr.write(self.style.ERROR("⚠️ Please provide --config file"))
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except UnicodeDecodeError:
            # Some editors add BOM; try utf-8-sig
            with open(config_path, "r", encoding="utf-8-sig") as f:
                config = yaml.safe_load(f) or {}

        
        # Resolve images_dir default: dir of YAML if not provided
        if not images_dir:
            images_dir = os.path.dirname(os.path.abspath(config_path))
        
        # Resolve timezone for naive datetimes
        tzinfo = timezone.get_current_timezone()
        tz_name = options.get("tz")
        if tz_name:
            try:
                # Prefer Python 3.9+'s zoneinfo if available
                try:
                    from zoneinfo import ZoneInfo  # py3.9+
                    tzinfo = ZoneInfo(tz_name)
                except Exception:
                    import pytz  # fallback
                    tzinfo = pytz.timezone(tz_name)
            except Exception:
                self.stderr.write(self.style.WARNING(f"Unknown timezone '{tz_name}', using project default."))

        if clear_first and not dry_run:
            self.stdout.write("🧹 Clearing existing News data...")
            NewsSubscriber.objects.all().delete()
            NewsReaction.objects.all().delete()
            NewsComment.objects.all().delete()
            NewsPost.objects.all().delete()
            NewsCategory.objects.all().delete()

        # Categories
        for cat in config.get("categories", []):
            category, created = NewsCategory.objects.get_or_create(
                slug=cat["slug"], defaults={"name": cat["name"], "description": cat.get("description", "")}
            )
            msg = f"{'Created' if created else 'Updated'} category: {category.name}"
            self.stdout.write(self.style.SUCCESS(msg) if not dry_run else f"[DRY] {msg}")

        # --- posts ---
        for post in config.get("posts", []):
            # --- normalize inputs ---
            raw_author_email = (post.get("author_email") or "").strip().lower()
            raw_category_slug = (post.get("category_slug") or "").strip().lower()
            raw_category_name = (post.get("category_name") or "").strip()

            # optional datetimes (you already have _aware_dt + tzinfo)
            yaml_published_on = self._aware_dt(post.get("published_on"), tzinfo)
            yaml_created_at  = self._aware_dt(post.get("created_at"), tzinfo)
            yaml_updated_at  = self._aware_dt(post.get("updated_at"), tzinfo)

            # status normalization
            raw_status = (post.get("status") or "PENDING").strip().upper()
            if raw_status not in {"DRAFT", "PENDING", "PUBLISHED"}:
                raw_status = "PENDING"

            # --- resolve author (case-insensitive) ---
            author = None
            if raw_author_email:
                author = User.objects.filter(email__iexact=raw_author_email).first()

            # (optional) fallback by username if provided
            if not author and post.get("author_username"):
                author = User.objects.filter(username__iexact=post["author_username"].strip()).first()

            # --- resolve category: prefer slug, fallback to name ---
            category = None
            if raw_category_slug:
                category = NewsCategory.objects.filter(slug__iexact=raw_category_slug).first()
            if not category and raw_category_name:
                category = NewsCategory.objects.filter(name__iexact=raw_category_name).first()

            # --- bail early with precise reason(s) ---
            missing = []
            if not author:
                missing.append(f"author={post.get('author_email') or post.get('author_username') or '<missing>'}")
            if not category:
                missing.append(f"category={post.get('category_slug') or post.get('category_name') or '<missing>'}")
            if missing:
                self.stderr.write(self.style.ERROR(
                    f"⚠️ Skipping post '{post.get('title') or '<untitled>'}' — missing: {', '.join(missing)}"
                ))
                continue

            # --- defaults for create/update ---
            defaults = {
                "title": post["title"],
                "author": author,
                "category": category,
                "summary": post.get("summary", ""),
                "content": post.get("content", ""),
                "status": raw_status,
                # If YAML provides published_on, use it; else auto if status is PUBLISHED
                "published_on": yaml_published_on if yaml_published_on else (
                    timezone.now() if raw_status == "PUBLISHED" else None
                ),
                "allow_comments": post.get("allow_comments", True),
            }

            if dry_run:
                when = defaults["published_on"].isoformat() if defaults["published_on"] else "None"
                self.stdout.write(
                    f"[DRY] Would create/update post: {post['title']} by {author.email} "
                    f"(category={category.slug}, status={raw_status}, published_on={when})"
                )
                continue

            obj, created = NewsPost.objects.update_or_create(
                slug=post["slug"].strip().lower(),   # normalize slug on write for consistency
                defaults=defaults,
            )

            # ---- image handling ----
            img_attached = False
            if post.get("image"):
                res = self._read_local_image(images_dir, post["image"])
                if res:
                    filename, content = res
                    self._attach_image(obj, "image", filename, content)
                    img_attached = True
                else:
                    self.stderr.write(self.style.WARNING(
                        f"Image not found: {post['image']} (base: {images_dir})"
                    ))

            elif post.get("image_url") and allow_download:
                res = self._download_image(post["image_url"])
                if res:
                    filename, content = res
                    self._attach_image(obj, "image", filename, content)
                    img_attached = True
                else:
                    self.stderr.write(self.style.WARNING(f"Failed to download image_url: {post['image_url']}"))

            # Save once more if we attached an image
            if img_attached:
                obj.save(update_fields=["image"])

            msg = f"{'Created' if created else 'Updated'} post: {obj.title} by {author.email}" + (" [with image]" if img_attached else "")
            self.stdout.write(self.style.SUCCESS(msg))

            # (optional) if you want to set created/updated explicitly when provided:
            # note: Django ignores auto_now*/auto_add* on direct assignment; use update_fields or queryset update
            if yaml_created_at or yaml_updated_at:
                update_fields = []
                if yaml_created_at:
                    obj.created_at = yaml_created_at
                    update_fields.append("created_at")
                if yaml_updated_at:
                    obj.updated_at = yaml_updated_at
                    update_fields.append("updated_at")
                if update_fields:
                    obj.save(update_fields=update_fields)
            
            msg = f"{'Created' if created else 'Updated'} post: {obj.title} by {author.email}"
            self.stdout.write(self.style.SUCCESS(msg))

        # --- comments ---
        for com in config.get("comments", []):
            user = User.objects.filter(email=com["user_email"]).first()
            post = NewsPost.objects.filter(slug=com["post_slug"]).first()
            if not user or not post:
                continue
            NewsComment.objects.get_or_create(
                post=post, user=user, content=com["content"],
                defaults={"is_approved": com.get("is_approved", True)}
            )
            self.stdout.write(f"Comment by {user.email} on {post.title}")

        # --- reactions ---
        for react in config.get("reactions", []):
            user = User.objects.filter(email=react["user_email"]).first()
            post = NewsPost.objects.filter(slug=react["post_slug"]).first()
            if not user or not post:
                continue
            NewsReaction.objects.update_or_create(
                post=post, user=user, defaults={"reaction": react["reaction"]}
            )
            self.stdout.write(f"Reaction by {user.email} on {post.title}")

        # --- subscribers ---
        for sub in config.get("subscribers", []):
            user = User.objects.filter(email__iexact=sub["user_email"]).first()
            category = NewsCategory.objects.filter(slug=sub.get("category_slug")).first() if sub.get("category_slug") else None
            author = User.objects.filter(email__iexact=sub.get("author_email")).first() if sub.get("author_email") else None

            if not user or (not category and not author):
                continue

            NewsSubscriber.objects.get_or_create(user=user, category=category, author=author)
            target = category.name if category else (author.get_full_name() or author.email)
            self.stdout.write(f"Subscription: {user.email} → {target}")

        self.stdout.write(self.style.SUCCESS("✅ News seeding completed!"))
