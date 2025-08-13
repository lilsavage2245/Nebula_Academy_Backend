# classes/serializers/base.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .fields import TimeSinceField, UserSafeField

User = get_user_model()


class TimestampedSerializerMixin(serializers.ModelSerializer):
    """
    Adds created_at as read-only and a human-readable 'time_since' field
    derived from created_at. Use where your model has created_at.
    """
    created_at = serializers.DateTimeField(read_only=True)
    time_since = TimeSinceField(source='created_at', read_only=True)

    class Meta:
        abstract = True


class OwnedByUserMixin(serializers.Serializer):
    """
    Adds:
      - user (read-only) -> compact, safe user representation
      - user_id (write-only) -> PK setter
    Also auto-fills user from request.user on create/update if not provided.
    """
    user = UserSafeField(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    def _attach_request_user_default(self, validated_data):
        request = self.context.get("request")
        if request and getattr(request, "user", None) and request.user.is_authenticated:
            # Only set if not explicitly provided in payload
            validated_data.setdefault("user", request.user)

    def create(self, validated_data):
        self._attach_request_user_default(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._attach_request_user_default(validated_data)
        return super().update(instance, validated_data)


class IdSlugReadOnlyMixin(serializers.ModelSerializer):
    """
    Common pattern for resources that expose id/slug but never allow writes.
    """
    id = serializers.IntegerField(read_only=True)
    slug = serializers.SlugField(read_only=True)

    class Meta:
        abstract = True
