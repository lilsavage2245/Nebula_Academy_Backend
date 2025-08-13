from rest_framework import viewsets


class DynamicSerializerMixin:
    """
    Use different serializers for different actions (e.g., list, create, retrieve).
    """
    serializer_action_classes = {}

    def get_serializer_class(self):
        return self.serializer_action_classes.get(self.action, self.serializer_class)


class OwnedByUserQuerySetMixin:
    """
    Limits queryset to objects owned by request.user.
    Used for subscriber, reactions, comments, etc.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        return qs.filter(user=user) if user.is_authenticated else qs.none()


class SoftDeleteMixin:
    """
    Generic soft-delete behavior for views where model has `is_active`.
    """
    def perform_destroy(self, instance):
        if hasattr(instance, 'is_active'):
            instance.is_active = False
            instance.save()
        else:
            super().perform_destroy(instance)
