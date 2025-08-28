# event/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q

from event.models import (
    EventCategory, Event, Speaker, EventSpeaker, EventRegistration
)

# ─── Event Category Admin ──────────────────────────────────────────────────────
@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


# ─── Inline Models ─────────────────────────────────────────────────────────────
class EventSpeakerInline(admin.TabularInline):
    model = EventSpeaker
    extra = 0
    fields = ('speaker_type', 'user', 'guest', 'role', 'speaker_order')
    autocomplete_fields = ('user', 'guest')
    ordering = ('speaker_order',)


class EventRegistrationInline(admin.TabularInline):
    """
    Inline moderation for registrations on the Event page.
    """
    model = EventRegistration
    extra = 0
    fields = (
        'display_attendee', 'email', 'phone_number',
        'status', 'attended', 'registered_at'
    )
    readonly_fields = ('display_attendee', 'registered_at')
    can_delete = False
    show_change_link = True

    def display_attendee(self, obj):
        # Prefer platform user name; fallback to guest first/last
        name = ''
        if obj.user:
            name = obj.user.get_full_name() or obj.user.email or ''
        if not name:
            name = f"{(obj.first_name or '').strip()} {(obj.last_name or '').strip()}".strip()
        return name or '-'
    display_attendee.short_description = "Attendee"


# ─── Event Admin ───────────────────────────────────────────────────────────────
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'event_type', 'format', 'target_group', 'status',
        'is_published', 'is_featured', 'start_datetime'
    )
    list_filter = (
        'event_type', 'format', 'target_group', 'status',
        'is_published', 'is_featured', 'category'
    )
    search_fields = ('title', 'description', 'venue', 'tags')
    autocomplete_fields = ('category', 'organizers')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('published_on', 'created_at', 'updated_at')
    date_hierarchy = 'start_datetime'
    ordering = ('-start_datetime',)
    inlines = [EventSpeakerInline, EventRegistrationInline]

    fieldsets = (
        (None, {
            'fields': (
                'title', 'slug', 'description', 'category',
                'event_type', 'target_group', 'audience_description',
                'format', 'status',
                'start_datetime', 'end_datetime',
                'event_link', 'venue', 'tags'
            )
        }),
        ('Publishing', {'fields': ('is_published', 'is_featured', 'published_on')}),
        ('Registration & Capacity', {'fields': ('is_registration_required', 'capacity', 'registration_deadline')}),
        ('Media', {'fields': ('banner_image', 'attached_file')}),
        ('Meta', {'fields': ('meta_title', 'meta_description')}),
        ('Organizers', {'fields': ('organizers',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


# ─── Speaker Admin ─────────────────────────────────────────────────────────────
@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'created_at')
    search_fields = ('name', 'bio')
    readonly_fields = ('created_at',)
    ordering = ('name',)


@admin.register(EventSpeaker)
class EventSpeakerAdmin(admin.ModelAdmin):
    list_display = ('event', 'display_speaker', 'role', 'speaker_order')
    list_filter = ('speaker_type',)
    search_fields = ('event__title', 'user__email', 'guest__name')
    autocomplete_fields = ('event', 'user', 'guest')
    ordering = ('event', 'speaker_order')

    def display_speaker(self, obj):
        if obj.speaker_type == obj.SpeakerType.USER and obj.user:
            return obj.user.get_full_name() or obj.user.email
        if obj.speaker_type == obj.SpeakerType.GUEST and obj.guest:
            return obj.guest.name
        return '-'
    display_speaker.short_description = 'Speaker'


# ─── Registration Admin ────────────────────────────────────────────────────────
@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    """
    Rich moderation UI for registrations (supports guests + users).
    """
    list_display = (
        'event',
        'display_name',
        'email',
        'status',
        'attended',
        'registered_at',
    )
    list_filter = (
        'status',
        'attended',
        'gender',
        'affiliation',
        'reason_for_attending',
        'event',
    )
    search_fields = (
        'event__title',
        'email',
        'first_name',
        'last_name',
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    autocomplete_fields = ('user', 'event')
    readonly_fields = ('registered_at', 'updated_at')
    ordering = ('-registered_at',)

    fieldsets = (
        ('Event / Link', {
            'fields': ('event', 'user')
        }),
        ('Attendee', {
            'fields': (
                'first_name', 'last_name', 'email', 'phone_number',
                'gender', 'gender_other', 'age',
                'affiliation', 'affiliation_other',
                'reason_for_attending', 'reason_other',
            )
        }),
        ('Moderation', {
            'fields': ('status', 'attended')
        }),
        ('Timestamps', {
            'fields': ('registered_at', 'updated_at')
        }),
    )

    actions = ['approve_selected', 'decline_selected', 'mark_attended_selected']

    # Display helpers
    def display_name(self, obj):
        if obj.user:
            return (obj.user.get_full_name() or obj.user.email or '').strip() or '-'
        name = f"{(obj.first_name or '').strip()} {(obj.last_name or '').strip()}".strip()
        return name or '-'
    display_name.short_description = "Attendee"

    # Bulk actions
    def approve_selected(self, request, queryset):
        updated = queryset.update(status=EventRegistration.RegistrationStatus.APPROVED)
        self.message_user(request, f"Approved {updated} registration(s).")
    approve_selected.short_description = "Approve selected registrations"

    def decline_selected(self, request, queryset):
        updated = queryset.update(status=EventRegistration.RegistrationStatus.REJECTED)
        self.message_user(request, f"Declined {updated} registration(s).")
    decline_selected.short_description = "Decline selected registrations"

    def mark_attended_selected(self, request, queryset):
        # (Optionally) enforce only approved can be attended:
        qs = queryset.filter(status=EventRegistration.RegistrationStatus.APPROVED)
        updated = qs.update(attended=True)
        skipped = queryset.count() - updated
        msg = f"Marked attended: {updated}."
        if skipped:
            msg += f" Skipped {skipped} (not APPROVED)."
        self.message_user(request, msg)
    mark_attended_selected.short_description = "Mark attended (approved only)"
