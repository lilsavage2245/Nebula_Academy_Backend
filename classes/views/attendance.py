# classes/views/attendance.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework import status

from classes.models import LessonAttendance
from classes.serializers.attendance import LessonAttendanceSerializer
from .base import (
    SoftDeleteMixin,
    DynamicSerializerMixin,
    FilteredLessonQuerysetMixin
)


class LessonAttendanceViewSet(
    SoftDeleteMixin,
    DynamicSerializerMixin,
    FilteredLessonQuerysetMixin,
    viewsets.ModelViewSet
):
    """
    Tracks lesson attendance:
    - Authenticated users can mark attendance once per lesson.
    - Staff can view and edit all records.
    - Soft deletion with ownership checks.
    """
    queryset = LessonAttendance.objects.select_related('lesson', 'user')
    serializer_class = LessonAttendanceSerializer
    write_serializer_class = LessonAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['lesson__title', 'user__email']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    @action(detail=True, methods=["patch"], url_path="track-progress")
    def track_progress(self, request, pk=None):
        """
        PATCH /api/classes/lesson-attendance/<id>/track-progress/
        Allows a user to send watched_percent and duration.
        Automatically updates attended_replay and attended if watched >= 95%.
        """
        instance = self.get_object()

        if request.user != instance.user:
            raise PermissionDenied("You can only update your own attendance record.")

        watched_percent = request.data.get("watched_percent")
        duration = request.data.get("duration")

        # Validate inputs
        try:
            if watched_percent is not None:
                watched_percent = float(watched_percent)
                if not 0 <= watched_percent <= 100:
                    return Response({"detail": "watched_percent must be between 0 and 100."}, status=400)
                instance.watched_percent = watched_percent

            if duration is not None:
                duration = int(duration)
                if duration < 0:
                    return Response({"detail": "duration must be non-negative."}, status=400)
                instance.duration = duration

        except (TypeError, ValueError):
            return Response({"detail": "Invalid input types."}, status=400)

        instance.update_attendance()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="mark-replay-watched")
    def mark_replay_watched(self, request, pk=None):
        instance = self.get_object()
        if request.user != instance.user and not request.user.is_staff:
            raise PermissionDenied("You can only mark your own attendance.")

        instance.attended_replay = True
        instance.update_attendance()
        return Response({"status": "Replay watched marked", "attended": instance.attended})

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        lesson = serializer.validated_data['lesson']

        if LessonAttendance.objects.filter(user=user, lesson=lesson).exists():
            raise PermissionDenied("You’ve already marked attendance for this lesson.")

        instance = serializer.save(user=user)
        instance.update_attendance()  # Updates `.attended` field

    def perform_update(self, serializer):
        user = self.request.user
        if not user.is_staff:
            raise PermissionDenied("Only staff can update attendance records.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not (user.is_staff or instance.user == user):
            raise PermissionDenied("You can only delete your own attendance record.")
        super().perform_destroy(instance)
