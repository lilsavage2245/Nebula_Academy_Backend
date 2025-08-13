# worksheet/views/worksheet.py

from rest_framework import viewsets, filters
from worksheet.models import Worksheet
from worksheet.serializers import (
    WorksheetSerializer,
    WorksheetCreateUpdateSerializer,
)
from worksheet.serializers.worksheet import WorksheetStaffSerializer
from common.permissions import IsLecturerOrVolunteerOrReadOnly


class WorksheetViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD and smart filtering for Worksheets.
    - Lookup by slug
    - Filters based on user role & audience
    - Staff and uploader can write
    """
    queryset = Worksheet.objects.filter(is_active=True).select_related('lesson', 'uploaded_by')
    permission_classes = [IsLecturerOrVolunteerOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'instructions']
    ordering_fields = ['created_at', 'due_date']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and not user.is_staff:
            # Role-aware audience filtering
            role = getattr(user, 'role', None)
            if role == 'FREE':
                return qs.filter(audience__in=['FREE', 'BOTH'])
            elif role == 'ENROLLED':
                return qs.filter(audience__in=['ENROLLED', 'BOTH'])
            else:
                return qs.filter(audience='BOTH')
        return qs

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WorksheetCreateUpdateSerializer
        if self.request.user.is_staff:
            return WorksheetStaffSerializer
        return WorksheetSerializer

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
