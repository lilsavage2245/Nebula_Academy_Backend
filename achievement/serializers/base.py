# achievement/serializers/base.py

from rest_framework import serializers


class TimestampedSerializerMixin(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True, required=False)


class ChoiceDisplayField(serializers.ChoiceField):
    """
    Adds a <field>_display to expose get_<field>_display()
    """
    def bind(self, field_name, parent):
        super().bind(field_name, parent)
        display_method = f'get_{field_name}_display'
        if hasattr(parent.Meta.model, display_method):
            parent.fields[f"{field_name}_display"] = serializers.SerializerMethodField()

    def get_attribute(self, instance):
        return instance

    def to_representation(self, value):
        return super().to_representation(value)
