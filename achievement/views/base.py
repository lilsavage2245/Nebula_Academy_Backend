# achievement/views/base.py

from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class SoftDeleteMixin:
    """
    Overrides destroy to soft-delete an object.
    Requires `is_active` on the model.
    """
    def perform_destroy(self, instance):
        if hasattr(instance, 'is_active'):
            instance.is_active = False
            instance.save()
        else:
            instance.delete()


class DynamicSerializerMixin:
    """
    Allows switching serializers based on action.
    Define `serializer_class` and optionally `write_serializer_class`.
    """
    def get_serializer_class(self):
        if hasattr(self, 'write_serializer_class') and self.action in ['create', 'update', 'partial_update']:
            return self.write_serializer_class
        return super().get_serializer_class()


class OwnedByUserQuerySetMixin:
    """
    Restrict queryset to the current user unless staff.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

class UserScopedQuerySetMixin:
    """
    Filters queryset based on:
    - `user_pk` from nested URL if user is staff.
    - Otherwise, uses request.user.

    Intended for use with DRF nested routers like:
    /api/users/{user_pk}/awarded/
    /api/users/{user_pk}/xp-events/
    """

    def get_queryset(self):
        qs = super().get_queryset()

        user = self.request.user
        user_pk = self.kwargs.get('user_pk')

        if user_pk:
            if user.is_staff:
                return qs.filter(user__pk=user_pk)
            raise PermissionDenied("You don't have permission to view another user's data.")

        return qs.filter(user=user)