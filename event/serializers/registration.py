# event/serializers/registration.py

from rest_framework import serializers
from django.utils.timesince import timesince
from django.utils.timezone import now

from event.models import EventRegistration, Event
from core.serializers import UserSerializer
from event.serializers.event import EventSerializer


# ─────────────────────────────────────────────────────────────────────────────
# READ SERIALIZER
# ─────────────────────────────────────────────────────────────────────────────
class EventRegistrationSerializer(serializers.ModelSerializer):
    """
    Public-facing serializer to display an event registration.
    """
    user = UserSerializer(read_only=True)
    event = EventSerializer(read_only=True)
    registered_since = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    affiliation_display = serializers.CharField(source='get_affiliation_display', read_only=True)
    reason_for_attending_display = serializers.CharField(source='get_reason_for_attending_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            # links
            'id', 'event', 'user',

            # attendee info
            'first_name', 'last_name', 'full_name', 'email', 'phone_number',
            'gender', 'gender_display', 'gender_other',
            'age',
            'affiliation', 'affiliation_display', 'affiliation_other',
            'reason_for_attending', 'reason_for_attending_display', 'reason_other',

            # workflow
            'status', 'status_display', 'attended',

            # timestamps
            'registered_at', 'registered_since', 'updated_at',
        ]
        read_only_fields = [
            'id', 'event', 'user',
            'status', 'status_display', 'attended',
            'registered_at', 'registered_since', 'updated_at',
        ]

    def get_registered_since(self, obj):
        return timesince(obj.registered_at) + " ago" if obj.registered_at else None

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


# ─────────────────────────────────────────────────────────────────────────────
# CREATE SERIALIZER (PUBLIC)
# ─────────────────────────────────────────────────────────────────────────────
class EventRegistrationCreateSerializer(serializers.ModelSerializer):
    """
    Public write serializer.
    - Accepts event via `event_id` or `event_slug`.
    - If the request user is authenticated, we link the `user` FK automatically and ignore any `email` duplicates for that user.
    - If anonymous, we require `first_name`, `last_name`, `email`.
    - Enforces capacity, deadline, and duplicate checks.
    """
    event_id = serializers.PrimaryKeyRelatedField(
        source='event',
        queryset=Event.objects.all(),
        required=False
    )
    event_slug = serializers.SlugRelatedField(
        source='event',
        slug_field='slug',
        queryset=Event.objects.all(),
        required=False
    )

    class Meta:
        model = EventRegistration
        # user is set implicitly (if authenticated)
        fields = [
            # event selector
            'event_id', 'event_slug',

            # attendee info
            'first_name', 'last_name', 'email', 'phone_number',
            'gender', 'gender_other',
            'age',
            'affiliation', 'affiliation_other',
            'reason_for_attending', 'reason_other',
        ]

    # ---------- field-level validation helpers ----------
    def _require_other_if_chosen(self, attrs, choice_field, other_field, label):
        if attrs.get(choice_field) == 'OTHER' and not (attrs.get(other_field) or '').strip():
            raise serializers.ValidationError({other_field: f"Please specify your {label.lower()}."})

    def validate(self, attrs):
        # Event presence
        event = attrs.get('event')
        if not event:
            raise serializers.ValidationError({"event": "Provide either event_id or event_slug."})

        # Enforce deadline / capacity
        if event.registration_deadline and now() > event.registration_deadline:
            raise serializers.ValidationError("The registration deadline has passed.")
        if event.is_full:
            raise serializers.ValidationError("This event has reached maximum capacity.")

        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None

        # If authenticated user → duplicate guard by (event, user)
        if user and user.is_authenticated:
            if EventRegistration.objects.filter(event=event, user=user).exists():
                raise serializers.ValidationError("You have already registered for this event.")
        else:
            # Anonymous / external → require attendee info
            for f in ('first_name', 'last_name', 'email'):
                if not (attrs.get(f) or '').strip():
                    raise serializers.ValidationError({f: "This field is required."})
            # Duplicate guard by (event, email)
            email = attrs.get('email').strip().lower()
            if EventRegistration.objects.filter(event=event, email__iexact=email).exists():
                raise serializers.ValidationError("This email is already registered for this event.")

        # OTHER choice companions
        self._require_other_if_chosen(attrs, 'gender', 'gender_other', 'Gender')
        self._require_other_if_chosen(attrs, 'affiliation', 'affiliation_other', 'Affiliation')
        self._require_other_if_chosen(attrs, 'reason_for_attending', 'reason_other', 'Reason for attending')

        return attrs

    def create(self, validated_data):
        """
        Create as PENDING by default; link `user` if authenticated.
        """
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None

        # Pop event from validated data
        event = validated_data.pop('event')

        # If logged-in user, link FK and (optionally) default names/email from profile if not provided
        if user and user.is_authenticated:
            # Avoid overriding explicit submissions; only backfill if missing
            validated_data.setdefault('first_name', getattr(user, 'first_name', '') or '')
            validated_data.setdefault('last_name', getattr(user, 'last_name', '') or '')
            validated_data.setdefault('email', getattr(user, 'email', '') or '')
            instance = EventRegistration.objects.create(event=event, user=user, **validated_data)
        else:
            # Pure guest registration
            instance = EventRegistration.objects.create(event=event, **validated_data)

        # Status defaults to PENDING via model; keep it that way here.
        return instance


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN UPDATE SERIALIZER
# ─────────────────────────────────────────────────────────────────────────────
class EventRegistrationAdminUpdateSerializer(serializers.ModelSerializer):
    """
    Staff-only serializer to approve/decline and mark attendance.
    """
    class Meta:
        model = EventRegistration
        fields = [
            'status',    # PENDING / APPROVED / REJECTED
            'attended',  # True/False
        ]

    def validate(self, attrs):
        # Optionally prevent attended=True unless APPROVED
        new_status = attrs.get('status', getattr(self.instance, 'status', None))
        attended = attrs.get('attended', getattr(self.instance, 'attended', False))
        if attended and new_status != EventRegistration.RegistrationStatus.APPROVED:
            raise serializers.ValidationError("Only approved registrations can be marked as attended.")
        return attrs
