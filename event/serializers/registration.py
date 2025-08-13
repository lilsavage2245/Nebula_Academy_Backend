# event/serializers/registration.py

from rest_framework import serializers
from django.utils.timesince import timesince
from django.utils.timezone import now

from event.models import EventRegistration
from core.serializers import UserSerializer
from event.serializers.event import EventSerializer


class EventRegistrationSerializer(serializers.ModelSerializer):
    """
    Public-facing serializer for displaying a user's event registration.
    """
    user = UserSerializer(read_only=True)
    event = EventSerializer(read_only=True)
    registered_since = serializers.SerializerMethodField()

    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event', 'user',
            'registered_at', 'registered_since',
            'attended', 'feedback_submitted'
        ]
        read_only_fields = fields

    def get_registered_since(self, obj):
        return timesince(obj.registered_at) + " ago" if obj.registered_at else None


class EventRegistrationCreateSerializer(serializers.ModelSerializer):
    """
    Used for registering a user to an event (write-only).
    """
    event_id = serializers.PrimaryKeyRelatedField(
        source='event',
        queryset=EventRegistration._meta.get_field('event').related_model.objects.all()
    )

    class Meta:
        model = EventRegistration
        fields = ['event_id']

    def validate(self, attrs):
        user = self.context['request'].user
        event = attrs.get('event')

        if EventRegistration.objects.filter(user=user, event=event).exists():
            raise serializers.ValidationError("You have already registered for this event.")

        if event.is_full:
            raise serializers.ValidationError("This event has reached maximum capacity.")

        if event.registration_deadline and now() > event.registration_deadline:
            raise serializers.ValidationError("The registration deadline has passed.")

        return attrs

    def create(self, validated_data):
        return EventRegistration.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
