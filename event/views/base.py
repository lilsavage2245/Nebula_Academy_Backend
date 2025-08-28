# event/views/base.py
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from django.shortcuts import get_object_or_404
from event.models import Event

from event.models.base import EventStatus


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow read-only for all, write for staff."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class StatusFilterMixin:
    """Filter to only published events for non-staff."""
    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, 'user', None)
        if not (user and user.is_authenticated and user.is_staff):
            now = timezone.now()
            return qs.filter(is_published=True, published_on__lte=now)
        return qs


class DynamicSerializerMixin:
    """Switch between `serializer_class` and `write_serializer_class`."""
    write_serializer_class = None
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update'] and self.write_serializer_class:
            return self.write_serializer_class
        return super().get_serializer_class()


class OwnedByUserQuerySetMixin:
    """Restrict list/retrieve to own objects for non-staff."""
    user_field = 'user'
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and not user.is_staff:
            return qs.filter(**{self.user_field: user})
        return qs

class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_staff


class EventQueryParamMixin:
    def get_event_from_query(self):
        from event.models import Event
        event_id = self.request.query_params.get('event')
        event_slug = self.request.query_params.get('event_slug')
        if event_id:
            return Event.objects.filter(id=event_id).first()
        if event_slug:
            return Event.objects.filter(slug=event_slug).first()
        return None

class EventScopedQuerysetMixin:
    """
    If this view is nested under /events/<slug>/..., restrict queryset to that event.
    Works with rest_framework_nested.* where the kwarg is 'event_pk'.
    If your EventViewSet.lookup_field='slug', event_pk is the slug.
    """
    event_lookup_url_kwarg = 'event_pk'  # from NestedDefaultRouter
    event_lookup_field = 'slug'          # must match EventViewSet.lookup_field

    def get_event(self):
        event_key = self.kwargs.get(self.event_lookup_url_kwarg)
        if not event_key:
            return None
        lookup = {self.event_lookup_field: event_key}
        return get_object_or_404(Event, **lookup)

    def get_queryset(self):
        qs = super().get_queryset()
        event = self.get_event()
        if event is not None:
            qs = qs.filter(event=event)
        return qs