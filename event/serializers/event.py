# event/serializers/event.py

from rest_framework import serializers
from django.utils.timesince import timesince
from django.utils import timezone

from event.models import Event
from event.serializers.category import EventCategorySerializer
from event.serializers.speaker import EventSpeakerSerializer, EventSpeakerCreateSerializer
from event.serializers.base import TimestampedSerializerMixin, ChoiceDisplayField
from core.serializers import UserSerializer


class EventSerializer(TimestampedSerializerMixin, serializers.ModelSerializer):
    category = EventCategorySerializer(read_only=True)
    organizers = UserSerializer(many=True, read_only=True)
    speakers = EventSpeakerSerializer(source='event_speakers', many=True, read_only=True)

    event_type = ChoiceDisplayField(choices=Event.EventType.choices)
    target_group = ChoiceDisplayField(choices=Event.EventTargetGroup.choices)
    format = ChoiceDisplayField(choices=Event.EventFormat.choices)
    status = ChoiceDisplayField(choices=Event.EventStatus.choices)

    published_on_display = serializers.SerializerMethodField()
    time_until_start = serializers.SerializerMethodField()
    computed_status = serializers.CharField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    speakers_list = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description', 'category',
            'event_type', 'event_type_display',
            'target_group', 'target_group_display',
            'audience_description',
            'format', 'format_display',
            'status', 'status_display', 'computed_status',
            'start_datetime', 'end_datetime',
            'event_link', 'venue',
            'tags', 'banner_image', 'attached_file',
            'is_published', 'is_featured', 'published_on', 'published_on_display',
            'is_registration_required', 'capacity', 'registration_deadline',
            'organizers', 'speakers', 'speakers_list',
            'meta_title', 'meta_description',
            'is_full',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'slug', 'published_on_display', 'computed_status', 'speakers_list',
            'is_full', 'created_at', 'updated_at'
        ]

    def get_published_on_display(self, obj):
        return timesince(obj.published_on) + " ago" if obj.published_on else None

    def get_time_until_start(self, obj):
        if obj.start_datetime:
            return timesince(timezone.now(), obj.start_datetime) + ' until start'
        return None

    def get_speakers_list(self, obj):
        return [str(s) for s in obj.event_speakers.all()]


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Event._meta.get_field('category').related_model.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    organizer_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Event._meta.get_field('organizers').related_model.objects.all(),
        source='organizers',
        write_only=True,
        required=False
    )
    speakers = EventSpeakerCreateSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Event
        exclude = ['slug', 'published_on', 'created_at', 'updated_at']

    def create(self, validated_data):
        speakers_data = validated_data.pop('speakers', [])
        event = super().create(validated_data)
        for speaker_data in speakers_data:
            speaker_data['event'] = event
            serializer = EventSpeakerCreateSerializer(data=speaker_data, context=self.context)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return event
