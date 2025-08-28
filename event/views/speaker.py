# event/views/speaker.py

from rest_framework import viewsets, filters
from event.models import Speaker, EventSpeaker
from event.serializers.speaker import (
    SpeakerSerializer,
    EventSpeakerSerializer,
    EventSpeakerCreateSerializer
)
from .base import DynamicSerializerMixin, IsAdminOrReadOnly, IsStaffOrReadOnly, EventScopedQuerysetMixin


class SpeakerViewSet(EventScopedQuerysetMixin, DynamicSerializerMixin, viewsets.ModelViewSet):
    """
    Manage guest speakers (non-platform users).
    
    - Staff can create/update/delete.
    - Anyone can view.
    - Supports search, ordering, and slug-based lookup.
    """
    queryset = Speaker.objects.all()
    serializer_class = SpeakerSerializer
    permission_classes = [IsStaffOrReadOnly]

    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'bio']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']


class EventSpeakerViewSet(DynamicSerializerMixin, viewsets.ModelViewSet):
    """
    Manage assignment of speakers (platform users or guests) to events.

    - Staff-only access.
    - Can filter by ?event=<id> or ?event_slug=<slug>.
    - Supports ordering and role-based search.
    """
    queryset = EventSpeaker.objects.select_related('user', 'guest', 'event')
    serializer_class = EventSpeakerSerializer
    write_serializer_class = EventSpeakerCreateSerializer
    permission_classes = [IsStaffOrReadOnly]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['role', 'user__email', 'guest__name', 'event__title']
    ordering_fields = ['speaker_order', 'role']
    ordering = ['speaker_order']
    lookup_field = 'id'

    def get_queryset(self):
        qs = super().get_queryset()
        event_slug = self.kwargs.get('event_slug') or self.request.query_params.get('event_slug')
        if event_slug:
            qs = qs.filter(event__slug=event_slug)
        return qs
