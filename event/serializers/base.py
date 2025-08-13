# event/serializers/base.py

from rest_framework import serializers


class TimestampedSerializerMixin:
    """
    Adds created_at and updated_at fields if present on the model.
    Use this on serializers where the model has these fields.
    """
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ChoiceDisplayField(serializers.ChoiceField):
    """
    When used on a model choice field, adds an extra field <field>_display
    to expose the human-readable version via `get_<field>_display`.
    """

    def __init__(self, choices, **kwargs):
        super().__init__(choices=choices, **kwargs)

    def bind(self, field_name, parent):
        super().bind(field_name, parent)
        display_method = f'get_{field_name}_display'
        if hasattr(parent.Meta.model, display_method):
            parent.fields[f'{field_name}_display'] = serializers.CharField(
                source=display_method, read_only=True
            )
