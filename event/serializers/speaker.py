# event/serializers/speaker.py

from rest_framework import serializers
from event.models import Speaker, EventSpeaker
from core.serializers import UserSerializer
from .base import TimestampedSerializerMixin, ChoiceDisplayField


class SpeakerSerializer(TimestampedSerializerMixin, serializers.ModelSerializer):
    """
    Guest speaker (non-platform user) serializer.
    """
    class Meta:
        model = Speaker
        fields = [
            'id', 'name', 'bio', 'profile_image', 'website',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EventSpeakerSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for speaker info attached to an event.
    Includes both guest and platform speakers.
    """
    speaker_type = ChoiceDisplayField(choices=EventSpeaker.SpeakerType.choices)
    user = UserSerializer(read_only=True)
    guest = SpeakerSerializer(read_only=True)

    class Meta:
        model = EventSpeaker
        fields = [
            'id', 'event', 'speaker_type', 'speaker_type_display',
            'user', 'guest', 'role', 'speaker_order'
        ]
        read_only_fields = ['id', 'user', 'guest', 'speaker_type_display']


class EventSpeakerCreateSerializer(serializers.ModelSerializer):
    """
    Used for admin/staff input when assigning a speaker to an event.
    Ensures only the correct speaker type is used per entry.
    """
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=EventSpeaker._meta.get_field('user').remote_field.model.objects.all(),
        source='user',
        required=False
    )
    guest_id = serializers.PrimaryKeyRelatedField(
        queryset=Speaker.objects.all(),
        source='guest',
        required=False
    )

    class Meta:
        model = EventSpeaker
        fields = [
            'event', 'speaker_type', 'user_id', 'guest_id',
            'role', 'speaker_order'
        ]

    def validate(self, attrs):
        speaker_type = attrs.get('speaker_type')
        user = attrs.get('user')
        guest = attrs.get('guest')

        if speaker_type == EventSpeaker.SpeakerType.USER and not user:
            raise serializers.ValidationError("Platform user must be provided for USER speaker type.")
        if speaker_type == EventSpeaker.SpeakerType.GUEST and not guest:
            raise serializers.ValidationError("Guest speaker must be provided for GUEST speaker type.")
        return attrs
