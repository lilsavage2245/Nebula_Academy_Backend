# worksheet/serializers/base.py
from rest_framework import serializers


class TimestampedSerializerMixin:
    """
    Adds created_at and updated_at if model has them.
    """
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ChoiceDisplayField(serializers.ChoiceField):
    """
    Adds <field>_display field to expose `get_<field>_display()` on model.
    """
    def bind(self, field_name, parent):
        super().bind(field_name, parent)
        display_method = f'get_{field_name}_display'
        if hasattr(parent.Meta.model, display_method):
            parent.fields[f"{field_name}_display"] = serializers.CharField(
                source=display_method, read_only=True
            )
