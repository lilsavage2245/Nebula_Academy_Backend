# classes/views/lesson.py

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from classes.models import Lesson, LessonMaterial
from classes.serializers.lesson import (
    LessonSerializer,
    LessonCreateUpdateSerializer,
    LessonMaterialSerializer
)
from .base import (
    SoftDeleteMixin,
    DynamicSerializerMixin,
    FilteredLessonQuerysetMixin
)
from common.permissions import IsAdminOnlyOrReadOnly, IsAdminOrLecturerOrReadOnly, IsLecturerOrVolunteerOrReadOnly  # assumes custom perms


class LessonViewSet(
    SoftDeleteMixin,
    DynamicSerializerMixin,
    FilteredLessonQuerysetMixin,
    viewsets.ModelViewSet
):
    """
    Lesson CRUD – staff can create/edit, students can view.
    """
    queryset = Lesson.objects.filter(is_active=True).select_related(
        'program_level', 'module', 'session'
    ).prefetch_related('materials', 'comments', 'ratings')
    permission_classes = [IsAdminOrLecturerOrReadOnly, IsLecturerOrVolunteerOrReadOnly]
    serializer_class = LessonSerializer
    write_serializer_class = LessonCreateUpdateSerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'created_at', 'title']
    ordering = ['-date']


class LessonMaterialViewSet(
    SoftDeleteMixin,
    DynamicSerializerMixin,
    viewsets.ModelViewSet
):
    """
    Materials upload/update. Only allowed if user is staff or lecturer.
    """
    queryset = LessonMaterial.objects.filter(is_active=True).select_related('lesson', 'uploaded_by')
    serializer_class = LessonMaterialSerializer
    permission_classes = [IsAdminOrLecturerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['created_at', 'version']
    ordering = ['-created_at']

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        lesson_slug = self.kwargs.get('lesson_slug') or self.request.query_params.get('lesson')
        if lesson_slug:
            qs = qs.filter(lesson__slug=lesson_slug)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        lesson = serializer.validated_data.get('lesson')

        # Allow only staff, session director, or assigned lecturers
        if not user.is_staff:
            if lesson.session and hasattr(lesson.session, 'director'):
                if user == lesson.session.director:
                    pass
                elif lesson.module.modulelecturer_set.filter(lecturer=user).exists():
                    pass
                else:
                    raise PermissionDenied("You do not have permission to upload materials for this lesson.")
            else:
                raise PermissionDenied("You do not have permission to upload materials.")
        
        serializer.save(uploaded_by=user)
