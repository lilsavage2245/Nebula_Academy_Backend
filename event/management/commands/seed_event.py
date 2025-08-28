# event/management/commands/seed_event.py
import os
import re
import sys
import yaml
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from event.models import (
    EventCategory, Event, Speaker, EventSpeaker, EventRegistration
)
from event.models.base import EventType, EventTargetGroup, EventFormat, EventStatus
from django.db.models import Q

def user_has_field(field_name: str) -> bool:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        User._meta.get_field(field_name)
        return True
    except Exception:
        return False

# Build a Q() that ORs across whatever identifiers your User model supports
def user_identifier_q(identifier: str) -> Q:
    identifier = (identifier or "").strip()
    if not identifier:
        return Q(pk=None)  # matches nothing
    fields = []
    # Prefer email
    if user_has_field("email"):
        fields.append(("email__iexact", identifier))
    # Try common alternates if present on your model
    if user_has_field("username"):
        fields.append(("username__iexact", identifier))
    if user_has_field("slug"):
        fields.append(("slug__iexact", identifier))

    q = Q(pk=None)
    for lookup, value in fields:
        q = q | Q(**{lookup: value})
    return q

def users_from_identifiers(identifiers: list):
    """Return queryset of users matching ANY of the identifiers across supported fields."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    q = Q(pk=None)
    for ident in identifiers or []:
        q |= user_identifier_q(ident)
    return User.objects.filter(q)



# ---------- helpers ----------

RELATIVE_RE = re.compile(
    r'^(?P<sign>[+-])(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?(?::?(?P<minutes>\d+)m)?(?:\s+(?P<time>\d{1,2}:\d{2}))?$'
)
ISO_ENDINGS = ('Z', '+00:00')

def coerce_reg_choice(val, enum):
    if not val:
        return ''
    val = val.upper()
    valid = {c[0] for c in enum.choices}
    if val not in valid:
        raise CommandError(f"Invalid value '{val}' for {enum.__name__}. Allowed: {sorted(valid)}")
    return val

def parse_dt(value: str) -> datetime:
    """
    Accepts:
      - ISO 8601: '2025-08-21T14:00:00Z' / '2025-08-21 14:00'
      - Relative: '+7d 15:00', '-2d', '+3d2h', '+1d 09:30'
    Interprets naive datetimes as timezone-aware in current TZ.
    """
    if not isinstance(value, str):
        raise ValueError("Datetime must be a string.")

    m = RELATIVE_RE.match(value.strip())
    if m:
        now = timezone.now()
        sign = 1 if m.group('sign') == '+' else -1
        days = int(m.group('days') or 0)
        hours = int(m.group('hours') or 0)
        minutes = int(m.group('minutes') or 0)
        when = now + sign * timedelta(days=days, hours=hours, minutes=minutes)
        t = m.group('time')
        if t:
            hh, mm = t.split(':')
            when = when.astimezone(timezone.get_current_timezone()).replace(
                hour=int(hh), minute=int(mm), second=0, microsecond=0
            )
            when = timezone.make_aware(when.replace(tzinfo=None), timezone.get_current_timezone())
        return when

    # ISO-ish
    try:
        # Try strict ISO with timezone
        if value.endswith(ISO_ENDINGS):
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt if timezone.is_aware(dt) else timezone.make_aware(dt, timezone.utc)
        # Try flexible parse
        try:
            dt = datetime.fromisoformat(value)
        except Exception:
            # Fallback: allow space in place of 'T'
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M")
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
    except Exception as e:
        raise ValueError(f"Could not parse datetime '{value}': {e}")


def load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise CommandError(f"Config file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}



def coerce_choice(value: Optional[str], choices_enum, field_name: str) -> Optional[str]:
    if value is None:
        return None
    value = value.upper()
    valid = {c[0] for c in choices_enum.choices}
    if value not in valid:
        raise CommandError(f"Invalid {field_name} '{value}'. Allowed: {sorted(valid)}")
    return value


def attach_file_field(instance, field_name: str, path: Optional[str], base_dir: Optional[str] = None):
    """
    Attach a file/image from disk path if present.
    - Accepts Windows or POSIX separators.
    - Resolves relative paths against `base_dir` (usually the YAML's directory),
      falling back to CWD if base_dir not provided.
    """
    if not path:
        return
    # Normalize slashes and collapse .., .
    norm = os.path.normpath(path.replace('\\', '/'))

    # Make absolute: prefer base_dir (config folder), else CWD
    if not os.path.isabs(norm):
        root = base_dir or os.getcwd()
        norm = os.path.abspath(os.path.join(root, norm))

    if not os.path.exists(norm):
        raise CommandError(f"File not found for {field_name}: {path} -> {norm}")

    with open(norm, 'rb') as f:
        content = ContentFile(f.read())
        getattr(instance, field_name).save(os.path.basename(norm), content, save=False)



# ---------- main command ----------

class Command(BaseCommand):
    help = "Seed events (categories, events, speakers, event-speakers, registrations) from a YAML config."

    def add_arguments(self, parser):
        parser.add_argument('--config', required=True, help='Path to YAML config file.')
        parser.add_argument('--dry-run', action='store_true', help='Print actions without writing to DB.')
        parser.add_argument('--reset', action='store_true', help='Delete existing seeded objects before seeding.')
        parser.add_argument('--publish-all', action='store_true', help='Force is_published=True and set published_on=now.')
        parser.add_argument('--limit', type=int, default=None, help='Limit number of events to create.')

    @transaction.atomic
    def handle(self, *args, **options):
        config_path = options['config']
        dry_run = options['dry_run']
        reset = options['reset']
        publish_all = options['publish_all']
        limit = options['limit']

        data = load_yaml(config_path)
        config_dir = os.path.dirname(os.path.abspath(config_path))

        # Expect top-level keys; default to empty lists
        categories = data.get('categories', [])
        speakers = data.get('speakers', [])
        events = data.get('events', [])
        registrations = data.get('registrations', [])

        if limit is not None:
            events = events[:limit]

        if reset:
            self._reset(dry_run)

        # Seed in order: categories -> speakers -> events -> event_speakers -> registrations
        created_summary = {
            'categories': 0, 'speakers': 0, 'events': 0, 'event_speakers': 0, 'registrations': 0
        }

        # Categories
        for c in categories:
            name = c['name'].strip()
            defaults = {'description': c.get('description', '').strip()}
            if dry_run:
                self.stdout.write(f"[DRY] Category upsert: {name}")
            else:
                obj, created = EventCategory.objects.update_or_create(name=name, defaults=defaults)
                created_summary['categories'] += int(created)

        # Speakers (guests)
        for s in speakers:
            name = s['name'].strip()
            defaults = {
                'bio': s.get('bio', '').strip(),
                'website': s.get('website', '').strip(),
            }
            if dry_run:
                self.stdout.write(f"[DRY] Speaker upsert: {name}")
            else:
                obj, created = Speaker.objects.update_or_create(name=name, defaults=defaults)
                # optional image
                image_path = s.get('profile_image_path')
                if image_path:
                    attach_file_field(obj, 'profile_image', image_path, base_dir=config_dir)  # << add base_dir
                    obj.save()

                created_summary['speakers'] += int(created)

        # Events
        user_model = get_user_model()
        slug_to_event = {}  # cache for linking later

        for e in events:
            # Description handling (supports plain, HTML, or Markdown)
            description = e.get('description', '') or ''
            description_format = (e.get('description_format') or '').lower()
            description_html = e.get('description_html')

            if description_html:
                # Trusting provided HTML (sanitize optionally below)
                final_description = description_html
            elif description and description_format == 'markdown':
                try:
                    import markdown2  # pip install markdown2
                    final_description = markdown2.markdown(description, extras=['fenced-code-blocks', 'tables'])
                except Exception:
                    # Fallback: store raw text if converter not available
                    final_description = description
            else:
                final_description = description

            # Optional: sanitize HTML if you want defense-in-depth
            # (only if you're storing HTML and rendering it as HTML on the site)
            sanitize = e.get('sanitize_html', True)  # allow override per event
            if description_html or description_format == 'markdown':
                if sanitize:
                    try:
                        import bleach
                        allowed_tags = bleach.sanitizer.ALLOWED_TAGS.union({
                            'p', 'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'blockquote', 'strong', 'em', 'a', 'br', 'hr'
                        })
                        allowed_attrs = {'a': ['href', 'title', 'target', 'rel']}
                        final_description = bleach.clean(final_description, tags=allowed_tags, attributes=allowed_attrs, strip=True)
                    except Exception:
                        # If bleach not installed, proceed unsanitized (or raise)
                        pass

            # Choices
            event_type = coerce_choice(e.get('event_type', 'OTHER'), EventType, 'event_type')
            target_group = coerce_choice(e.get('target_group', 'ALL'), EventTargetGroup, 'target_group')
            fmt = coerce_choice(e.get('format', 'ONLINE'), EventFormat, 'format')
            status = coerce_choice(e.get('status', 'UPCOMING'), EventStatus, 'status')

            # Category
            category_name = e.get('category_name')
            category_slug = e.get('category_slug')
            category = None
            if category_slug:
                category = EventCategory.objects.filter(slug=category_slug).first()
            elif category_name:
                category = EventCategory.objects.filter(name=category_name).first()
            if category_name and not category:
                raise CommandError(f"Category not found for event '{e.get('title')}': {category_name}")

            # Dates
            start_dt = parse_dt(e['start_datetime'])
            end_dt = parse_dt(e['end_datetime']) if e.get('end_datetime') else None

            # Basic fields
            title = (e.get('title') or '').strip()
            if not title:
                raise CommandError("Event requires a 'title'")
            slug = (e.get('slug') or '').strip()  # optional, but preferred for idempotent upserts
            lookup = {'slug': slug} if slug else {'title': title}
            final_desc = (locals().get('final_description') or e.get('description') or '').strip()
            description = e.get('description', '').strip()
            audience_description = e.get('audience_description', '').strip()
            event_link = e.get('event_link', '').strip()
            venue = e.get('venue', '').strip()
            tags = e.get('tags') or None
            is_published = bool(e.get('is_published', False) or publish_all)
            is_featured = bool(e.get('is_featured', False))
            is_registration_required = bool(e.get('is_registration_required', True))
            capacity = e.get('capacity')
            reg_deadline = parse_dt(e['registration_deadline']) if e.get('registration_deadline') else None
            meta_title = e.get('meta_title', '').strip()
            meta_description = e.get('meta_description', '').strip()

            # Organizers (by email or username)
            organizer_ids = e.get('organizers', []) or []
            organizer_qs = users_from_identifiers(organizer_ids)
            if organizer_ids:
                found_emails = set(organizer_qs.values_list('email', flat=True)) if user_has_field('email') else set()
                # Best-effort: mark any identifiers not resolved via any supported field
                resolved = set()
                if user_has_field('email'):
                    resolved |= set(organizer_qs.values_list('email', flat=True))
                if user_has_field('username'):
                    resolved |= set(organizer_qs.values_list('username', flat=True))
                if user_has_field('slug'):
                    resolved |= set(organizer_qs.values_list('slug', flat=True))
                missing = [i for i in organizer_ids if i not in resolved]
                if missing:
                    self.stdout.write(self.style.WARNING(f"Organizer identifier(s) not found: {sorted(set(missing))}"))
            self.stdout.write(self.style.SUCCESS(f"Organizer(s) found: {sorted(set(found_emails))}"))    

            if dry_run:
                self.stdout.write(f"[DRY] Event upsert: {title}")
                # Choose identifier: prefer slug if provided, else title
                slug = (e.get('slug') or '').strip()
                lookup = {'slug': slug} if slug else {'title': title}
                evt = None
            else:
                evt, created = Event.objects.update_or_create(
                    **lookup,
                    defaults=dict(
                        title=title,  # keep title in defaults so slugged upserts can also update title
                        description=final_description,   # << use rendered HTML/MD
                        category=category,
                        event_type=event_type,
                        target_group=target_group,
                        audience_description=audience_description,
                        format=fmt,
                        status=status,
                        start_datetime=start_dt,
                        end_datetime=end_dt,
                        event_link=event_link,
                        venue=venue,
                        tags=tags,
                        is_published=is_published,
                        is_featured=is_featured,
                        is_registration_required=is_registration_required,
                        capacity=capacity,
                        registration_deadline=reg_deadline,
                        meta_title=meta_title,
                        meta_description=meta_description,
                    )
                )
                created_summary['events'] += int(created)

                # Media (optional)
                attach_file_field(evt, 'banner_image', e.get('banner_image_path'), base_dir=config_dir)
                attach_file_field(evt, 'attached_file', e.get('attached_file_path'), base_dir=config_dir)
                evt.save()

                if organizer_qs.exists():
                    evt.organizers.set(organizer_qs)

                slug_to_event[evt.slug] = evt

            # Event speakers (inline under each event)
            for es in e.get('speakers', []):
                speaker_type = es.get('speaker_type', 'GUEST').upper()
                role = es.get('role', '').strip()
                speaker_order = int(es.get('speaker_order', 0))
                user_email = es.get('user_email')
                guest_name = es.get('guest_name')

                if dry_run:
                    self.stdout.write(f"[DRY]  - attach speaker ({speaker_type}): {user_email or guest_name}")
                    continue

                if speaker_type == EventSpeaker.SpeakerType.USER:
                    if not user_email:
                        raise CommandError(f"Missing user_email (or identifier) for USER speaker on event '{title}'")
                    user = users_from_identifiers([user_email]).first()
                    if not user:
                        raise CommandError(f"User speaker not found: {user_email}")
                    obj, created = EventSpeaker.objects.update_or_create(
                        event=evt, user=user, guest=None,
                        defaults={'speaker_type': EventSpeaker.SpeakerType.USER, 'role': role, 'speaker_order': speaker_order}
                    )

                else:
                    if not guest_name:
                        raise CommandError(f"Missing guest_name for GUEST speaker on event '{title}'")
                    guest, _ = Speaker.objects.get_or_create(name=guest_name)
                    obj, created = EventSpeaker.objects.update_or_create(
                        event=evt, user=None, guest=guest,
                        defaults={'speaker_type': EventSpeaker.SpeakerType.GUEST, 'role': role, 'speaker_order': speaker_order}
                    )
                created_summary['event_speakers'] += int(created)

        # Registrations (support platform users OR external guests)
        for r in registrations:
            # Resolve event
            event_slug = r.get('event_slug')
            event_title = r.get('event_title')
            evt = None
            if event_slug:
                evt = Event.objects.filter(slug=event_slug).first()
            elif event_title:
                evt = Event.objects.filter(title=event_title).first()
            if not evt:
                raise CommandError(f"Registration event not found (slug={event_slug} title={event_title})")

            # Optional status / attended
            status_val = r.get('status', 'PENDING')
            try:
                # Validate against your enum
                _ = EventRegistration.RegistrationStatus[status_val]
            except Exception:
                raise CommandError(f"Invalid registration status '{status_val}' (use PENDING/APPROVED/REJECTED)")
            attended_val = bool(r.get('attended', False))

            if dry_run:
                self.stdout.write(f"[DRY] Registration for event={evt.slug or evt.title}")
                continue

            # Try platform user path first (by email or username)
            user_identifier = r.get('user_email') or r.get('username') or r.get('user_id')
            if user_identifier:
                user = users_from_identifiers([user_identifier]).first()
                if not user:
                    raise CommandError(f"Registration user not found: {user_identifier}")
                obj, created = EventRegistration.objects.get_or_create(
                    event=evt,
                    user=user,
                    defaults={
                        'first_name': getattr(user, 'first_name', '') or '',
                        'last_name': getattr(user, 'last_name', '') or '',
                        'email': getattr(user, 'email', '') or '',
                        'status': status_val,
                        'attended': attended_val,
                    }
                )
                if not created:
                    obj.status = status_val
                    obj.attended = attended_val
                    obj.save(update_fields=['status', 'attended', 'updated_at'])
                created_summary['registrations'] += int(created)
                continue

            # Guest path (no user account)

            # 1) Accept either `email` or `guest_email` (alias)
            raw_email = (r.get('email') or r.get('guest_email') or '').strip()
            email = raw_email.lower()  # normalize for consistent uniqueness

            # 2) Split guest_name if present and first/last missing
            guest_name = (r.get('guest_name') or '').strip()
            first_name = (r.get('first_name') or '').strip()
            last_name  = (r.get('last_name') or '').strip()
            if guest_name and not (first_name or last_name):
                parts = guest_name.split()
                first_name = parts[0]
                last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''

            # 3) Require after alias + split
            if not (first_name and last_name and email):
                raise CommandError(
                    "Guest registration requires 'first_name', 'last_name', and 'email' "
                    "(you may also use 'guest_name' + 'guest_email')."
                )

            # 4) Optional choice fields (validate against enums)
            from event.models import EventRegistration as ER

            def coerce_reg_choice(val, enum):
                if not val:
                    return ''
                val = str(val).upper()
                valid = {c[0] for c in enum.choices}
                if val not in valid:
                    raise CommandError(f"Invalid value '{val}' for {enum.__name__}. Allowed: {sorted(valid)}")
                return val

            gender            = coerce_reg_choice((r.get('gender') or ''), ER.Gender) or ''
            gender_other      = (r.get('gender_other') or '').strip()
            affiliation       = coerce_reg_choice((r.get('affiliation') or ''), ER.Affiliation) or ''
            affiliation_other = (r.get('affiliation_other') or '').strip()
            reason            = coerce_reg_choice((r.get('reason_for_attending') or ''), ER.ReasonForAttending) or ''
            reason_other      = (r.get('reason_other') or '').strip()
            age               = r.get('age')
            phone_number      = (r.get('phone_number') or '').strip()

            # 5) Upsert by (event, email) for guests
            obj, created = EventRegistration.objects.get_or_create(
                event=evt,
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone_number': phone_number,
                    'gender': gender,
                    'gender_other': gender_other,
                    'age': age,
                    'affiliation': affiliation,
                    'affiliation_other': affiliation_other,
                    'reason_for_attending': reason,
                    'reason_other': reason_other,
                    'status': status_val,
                    'attended': attended_val,
                }
            )

            if not created:
                # Update mutable fields on reseed
                obj.first_name = first_name or obj.first_name
                obj.last_name = last_name or obj.last_name
                obj.phone_number = phone_number or obj.phone_number
                obj.gender = gender or obj.gender
                obj.gender_other = gender_other or obj.gender_other
                obj.age = age if age is not None else obj.age
                obj.affiliation = affiliation or obj.affiliation
                obj.affiliation_other = affiliation_other or obj.affiliation_other
                obj.reason_for_attending = reason or obj.reason_for_attending
                obj.reason_other = reason_other or obj.reason_other
                obj.status = status_val
                obj.attended = attended_val
                obj.save()

            created_summary['registrations'] += int(created)



        # Summary
        self.stdout.write(self.style.SUCCESS("Seeding complete." if not dry_run else "Dry-run complete."))
        self.stdout.write(self.style.NOTICE(f"Summary: {created_summary}"))

    def _reset(self, dry_run: bool):
        """
        Removes all Event-related objects. Order matters (FK constraints).
        """
        if dry_run:
            self.stdout.write("[DRY] Reset: deleting EventRegistration, EventSpeaker, Event, Speaker, EventCategory")
            return
        EventRegistration.objects.all().delete()
        EventSpeaker.objects.all().delete()
        Event.objects.all().delete()
        Speaker.objects.all().delete()
        EventCategory.objects.all().delete()
        self.stdout.write(self.style.WARNING("Reset complete: all event-related records deleted."))
