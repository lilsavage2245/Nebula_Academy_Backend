# event/views/event.py

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from event.models import Event
from event.serializers.event import EventSerializer, EventCreateUpdateSerializer
from .base import (
    StatusFilterMixin,
    DynamicSerializerMixin,
    IsAdminOrReadOnly,
)


class EventViewSet(
    StatusFilterMixin,
    DynamicSerializerMixin,
    viewsets.ModelViewSet
):
    """
    Handles listing, retrieving, creating, updating, and publishing events.

    - Public users see only published events (via StatusFilterMixin).
    - Staff can create/update events.
    - Admins can publish events via a custom action.
    - Searchable and filterable by key event fields.
    """
    queryset = Event.objects.select_related('category') \
                            .prefetch_related(
                                'organizers',
                                'event_speakers__user',
                                'event_speakers__guest'
                            ).all()

    serializer_class = EventSerializer
    write_serializer_class = EventCreateUpdateSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'event_type', 'target_group', 'format', 'status',
        'category', 'is_published', 'is_featured'
    ]
    search_fields = ['title', 'description', 'audience_description', 'venue', 'tags']
    ordering_fields = ['start_datetime', 'end_datetime', 'created_at', 'updated_at']
    ordering = ['-start_datetime']

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrReadOnly])
    def publish(self, request, slug=None):
        """
        Publish an event manually. Only for staff/admin use.
        """
        event = self.get_object()
        if not event.is_published:
            event.is_published = True
            event.published_on = timezone.now()
            event.save(update_fields=['is_published', 'published_on'])
        return Response(EventSerializer(event).data, status=status.HTTP_200_OK)
