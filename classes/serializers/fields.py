# serializers/fields.py

from rest_framework import serializers
from django.utils.timesince import timesince


class DisplayChoiceField(serializers.ChoiceField):
    def to_representation(self, value):
        if value == '' and self.allow_blank:
            return {'value': value, 'display': value}
        if value is None:
            return value
        return {
            'value': value,
            'display': self.choice_strings_to_display.get(str(value), str(value))
        }

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = data.get('value', '')
        return super().to_internal_value(data)


class UserSafeField(serializers.ReadOnlyField):
    def to_representation(self, user):
        return {
            'name': user.get_full_name(),
            'email': user.email,
            'role': getattr(user, 'role', 'Student')
        }



class TimeSinceField(serializers.ReadOnlyField):
    def to_representation(self, value):
        if not value:
            return None
        return timesince(value) + " ago"
