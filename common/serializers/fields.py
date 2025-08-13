# common/serializers/fields.py

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

class ContentTypeField(serializers.SlugRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault('slug_field', 'model')
        kwargs.setdefault('queryset', ContentType.objects.all())  # ✅ set real queryset
        super().__init__(**kwargs)

    def to_representation(self, obj):
        return obj.model

    def to_internal_value(self, data):
        try:
            return ContentType.objects.get(model=data)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(f"Invalid content type: '{data}'")
