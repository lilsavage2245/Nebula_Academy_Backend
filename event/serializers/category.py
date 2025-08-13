# event/serializers/category.py

from rest_framework import serializers
from event.models import EventCategory
from event.serializers.base import TimestampedSerializerMixin


class EventCategorySerializer(TimestampedSerializerMixin, serializers.ModelSerializer):
    """
    Public-facing serializer for displaying event categories.
    """
    class Meta:
        model = EventCategory
        fields = ['id', 'name', 'slug', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class EventCategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Used for admin or staff forms to create/update event categories.
    """
    class Meta:
        model = EventCategory
        fields = ['name', 'description']

