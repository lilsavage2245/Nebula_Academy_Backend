# event/views/registration.py

from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from event.models import EventRegistration
from event.serializers.registration import (
    EventRegistrationSerializer,
    EventRegistrationCreateSerializer
)
from .base import DynamicSerializerMixin, OwnedByUserQuerySetMixin


class EventRegistrationViewSet(
    DynamicSerializerMixin,
    OwnedByUserQuerySetMixin,
    viewsets.ModelViewSet
):
    """
    Handles event registration for users and admin staff.

    - Authenticated users can:
        - Register via `/register/`
        - Unregister via `/unregister/`
        - View their registrations via `/my-registrations/`
    - Staff can view all, search, and manage.
    """
    queryset = EventRegistration.objects.select_related('user', 'event')
    serializer_class = EventRegistrationSerializer
    write_serializer_class = EventRegistrationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    user_field = 'user'
    http_method_names = ['get', 'post', 'delete']

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['event__title', 'user__email']
    ordering_fields = ['registered_at']
    ordering = ['-registered_at']

    def destroy(self, request, *args, **kwargs):
        """
        Unregister from an event (DELETE /<pk>/).
        Only owner or staff can unregister.
        """
        reg = self.get_object()
        if not (request.user.is_staff or reg.user == request.user):
            raise PermissionDenied("You can only unregister yourself.")
        reg.delete()
        return Response({'message': 'Unregistered successfully.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        """
        Register the current user to an event.
        POST /event-registrations/register/
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(EventRegistrationSerializer(instance).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='unregister')
    def unregister(self, request, pk=None):
        """
        Unregister from a specific event registration.
        POST /event-registrations/<pk>/unregister/
        """
        reg = self.get_object()
        if not (request.user.is_staff or reg.user == request.user):
            raise PermissionDenied("You cannot unregister another user.")
        reg.delete()
        return Response({'message': 'Unregistered successfully.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='my-registrations')
    def my_registrations(self, request):
        """
        Return the current user's registrations.
        GET /event-registrations/my-registrations/
        """
        queryset = self.get_queryset().filter(user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
