# achievement/views/badge.py

from rest_framework import viewsets, permissions, filters
from achievement.models import Badge, AwardedBadge
from achievement.serializers.badge import (
    BadgeSerializer,
    BadgeCreateUpdateSerializer,
    AwardedBadgeSerializer,
    AwardedBadgeCreateSerializer,
)
from common.permissions import IsAdminOnlyOrReadOnly
from .base import OwnedByUserQuerySetMixin, DynamicSerializerMixin, UserScopedQuerySetMixin


class BadgeViewSet(DynamicSerializerMixin, viewsets.ModelViewSet):
    """
    Staff can manage all badges. Public users see active, non-hidden ones.
    """
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    write_serializer_class = BadgeCreateUpdateSerializer
    permission_classes = [IsAdminOnlyOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['display_order', 'name', 'created_at']
    ordering = ['display_order']

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True, is_hidden=False)
        return qs


class AwardedBadgeViewSet(UserScopedQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    """
    Lists badges earned by the current user.
    """
    queryset = AwardedBadge.objects.select_related('user', 'badge')
    serializer_class = AwardedBadgeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['awarded_at']
    ordering = ['-awarded_at']
