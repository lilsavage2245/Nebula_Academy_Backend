# event/views/category.py

from rest_framework import viewsets
from event.models import EventCategory
from event.serializers.category import (
    EventCategorySerializer,
    EventCategoryCreateUpdateSerializer
)
from .base import IsAdminOrReadOnly


class EventCategoryViewSet(viewsets.ModelViewSet):
    """
    Event Category CRUD:
    - Anyone can list and retrieve categories.
    - Only staff can create, update, or delete.
    - Uses separate serializers for read vs write.
    """
    queryset = EventCategory.objects.all().order_by('name')
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = EventCategorySerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EventCategoryCreateUpdateSerializer
        return EventCategorySerializer
