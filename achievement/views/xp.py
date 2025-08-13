# achievement/views/xp.py

from rest_framework import viewsets, permissions, filters
from rest_framework.exceptions import PermissionDenied
from achievement.models import XPEvent
from achievement.serializers.xp import XPEventSerializer, XPEventCreateSerializer
from achievement.views.base import DynamicSerializerMixin, OwnedByUserQuerySetMixin, UserScopedQuerySetMixin


class XPEventViewSet(
    DynamicSerializerMixin,
    UserScopedQuerySetMixin,
    viewsets.ModelViewSet
):
    """
    Lists XP events for the current user.
    Staff can create XP manually (e.g., for mentorship, events, etc).

    - GET: All users see their XP logs
    - POST: Only staff can create XP events
    """
    queryset = XPEvent.objects.select_related('user', 'badge')
    serializer_class = XPEventSerializer
    write_serializer_class = XPEventCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['timestamp', 'xp']
    search_fields = ['action', 'user__email', 'badge__name']
    ordering = ['-timestamp']

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only staff can assign XP manually.")
        serializer.save()
