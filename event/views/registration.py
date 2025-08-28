# event/views/registration.py

from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, NotFound

from event.models import EventRegistration
from event.serializers.registration import (
    EventRegistrationSerializer,
    EventRegistrationCreateSerializer,
    EventRegistrationAdminUpdateSerializer,
)
from .base import DynamicSerializerMixin, OwnedByUserQuerySetMixin, EventScopedQuerysetMixin, IsStaffOrReadOnly


class EventRegistrationViewSet(
    EventScopedQuerysetMixin,
    DynamicSerializerMixin,
    OwnedByUserQuerySetMixin,
    viewsets.ModelViewSet
):
    """
    Event registrations:
    - Anyone can register via /registrations/register/ (AllowAny)
    - Authenticated users can view their own registrations
    - Staff can view/search all, approve/decline, and mark attendance
    """
    queryset = EventRegistration.objects.select_related('user', 'event')
    serializer_class = EventRegistrationSerializer
    write_serializer_class = EventRegistrationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]   # default; overridden per-action in get_permissions()
    user_field = 'user'
    http_method_names = ['get', 'post', 'delete', 'patch']

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['event__title', 'user__email', 'email', 'first_name', 'last_name']
    ordering_fields = ['registered_at', 'updated_at']
    ordering = ['-registered_at']

    # ─────────────────────────────────────────────────────────────────────────
    # Permissions: allow public register; staff controls elsewhere
    # ─────────────────────────────────────────────────────────────────────────
    def get_permissions(self):
        if self.action in ['register']:  # public registration
            return [permissions.AllowAny()]
        if self.action in ['partial_update', 'update', 'approve', 'decline', 'mark_attended']:
            return [permissions.IsAdminUser()]
        # list/retrieve/destroy/my-registrations default to authenticated only
        return super().get_permissions()

    # ─────────────────────────────────────────────────────────────────────────
    # Serializer switching: write vs read vs admin update
    # ─────────────────────────────────────────────────────────────────────────
    def get_serializer_class(self):
        if self.action in ['create', 'register']:
            return self.write_serializer_class
        if self.action in ['partial_update', 'update'] and self.request.user and self.request.user.is_staff:
            return EventRegistrationAdminUpdateSerializer
        return self.serializer_class

    # ─────────────────────────────────────────────────────────────────────────
    # Ownership rule for non-staff lists (keeps staff view global)
    # ─────────────────────────────────────────────────────────────────────────
    # OwnedByUserQuerySetMixin handles .get_queryset() to filter by user for non-staff.
    # Staff see all.

    # ─────────────────────────────────────────────────────────────────────────
    # DELETE: unregister (owner or staff)
    # ─────────────────────────────────────────────────────────────────────────
    def destroy(self, request, *args, **kwargs):
        reg = self.get_object()
        # Guests (no user) cannot authenticate; only staff can remove those
        if not (request.user.is_staff or reg.user == request.user):
            raise PermissionDenied("You can only unregister yourself.")
        reg.delete()
        return Response({'message': 'Unregistered successfully.'}, status=status.HTTP_204_NO_CONTENT)

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC REGISTER
    # ─────────────────────────────────────────────────────────────────────────
    @action(detail=False, methods=['post'], url_path='register', permission_classes=[permissions.AllowAny])
    def register(self, request):
        """
        Public registration endpoint.
        Accepts event via event_id or event_slug and attendee details.
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(EventRegistrationSerializer(instance).data, status=status.HTTP_201_CREATED)

    # ─────────────────────────────────────────────────────────────────────────
    # OWNER QUICK LIST
    # ─────────────────────────────────────────────────────────────────────────
    @action(detail=False, methods=['get'], url_path='my-registrations')
    def my_registrations(self, request):
        """
        Return the current authenticated user's registrations.
        (Guests without accounts cannot list—only staff can browse all.)
        """
        queryset = self.get_queryset().filter(user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(queryset, many=True)
        return Response(ser.data)

    # ─────────────────────────────────────────────────────────────────────────
    # STAFF ACTIONS: approve / decline / mark_attended
    # ─────────────────────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='approve', permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        reg = self.get_object()
        reg.status = EventRegistration.RegistrationStatus.APPROVED
        reg.save(update_fields=['status', 'updated_at'])
        return Response(EventRegistrationSerializer(reg).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='decline', permission_classes=[permissions.IsAdminUser])
    def decline(self, request, pk=None):
        reg = self.get_object()
        reg.status = EventRegistration.RegistrationStatus.REJECTED
        reg.save(update_fields=['status', 'updated_at'])
        return Response(EventRegistrationSerializer(reg).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='mark-attended', permission_classes=[permissions.IsAdminUser])
    def mark_attended(self, request, pk=None):
        reg = self.get_object()
        # Optional: Only approved can be marked attended (mirrors admin update serializer)
        if reg.status != EventRegistration.RegistrationStatus.APPROVED:
            raise PermissionDenied("Only approved registrations can be marked as attended.")
        reg.attended = True
        reg.save(update_fields=['attended', 'updated_at'])
        return Response(EventRegistrationSerializer(reg).data, status=status.HTTP_200_OK)
