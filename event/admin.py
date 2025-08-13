from django.contrib import admin
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
    model = EventRegistration
    extra = 0
    fields = ('user', 'registered_at', 'attended', 'feedback_submitted')
    readonly_fields = ('registered_at',)
    autocomplete_fields = ('user',)
    can_delete = False
    show_change_link = True


# ─── Event Admin ───────────────────────────────────────────────────────────────
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'format', 'target_group', 'status', 'is_published', 'is_featured', 'start_datetime')
    list_filter = ('event_type', 'format', 'target_group', 'status', 'is_published', 'is_featured', 'category')
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
        ('Publishing', {
            'fields': (
                'is_published', 'is_featured', 'published_on'
            )
        }),
        ('Registration & Capacity', {
            'fields': (
                'is_registration_required', 'capacity', 'registration_deadline'
            )
        }),
        ('Media', {
            'fields': ('banner_image', 'attached_file')
        }),
        ('Meta', {
            'fields': ('meta_title', 'meta_description')
        }),
        ('Organizers', {
            'fields': ('organizers',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
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
    list_display = ('event', 'user', 'registered_at', 'attended', 'feedback_submitted')
    list_filter = ('attended', 'feedback_submitted')
    search_fields = ('user__email', 'event__title')
    autocomplete_fields = ('user', 'event')
    readonly_fields = ('registered_at',)
    ordering = ('-registered_at',)

