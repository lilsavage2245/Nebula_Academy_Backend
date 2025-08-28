# classes/views/feedback.py
from rest_framework import viewsets, permissions, filters
from rest_framework.exceptions import PermissionDenied

from classes.models import LessonComment, LessonRating
from classes.serializers.feedback import (
    LessonCommentSerializer,
    LessonRatingSerializer,
    LessonCommentCreateSerializer
)
from .base import (
    SoftDeleteMixin,
    DynamicSerializerMixin,
    FilteredLessonQuerysetMixin
)


class LessonCommentViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    """
    Threaded comments:
    - POST with {lesson, content} to add a root comment.
    - POST with {lesson, parent, content} to reply to any comment.
    - GET lists comments; use ?lesson=<id|slug> to filter.
    """
    queryset = LessonComment.objects.select_related('user', 'lesson').prefetch_related('replies')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering = ['created_at']

    def get_serializer_class(self):
        return LessonCommentCreateSerializer if self.action in ['create', 'update', 'partial_update'] \
               else LessonCommentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        lesson = self.request.query_params.get('lesson')
        root_only = self.request.query_params.get('root_only')
        if lesson:
            # Accept id or slug; adjust to your actual lesson lookup
            if lesson.isdigit():
                qs = qs.filter(lesson_id=int(lesson))
            else:
                qs = qs.filter(lesson__slug=lesson)
        if root_only in ('1', 'true', 'True'):
            qs = qs.filter(parent__isnull=True)
        return qs

    def perform_create(self, serializer):
        # If lesson disallows comments, enforce here if you track allow_comments per lesson
        lesson = serializer.validated_data['lesson']
        if hasattr(lesson, 'allow_comments') and not lesson.allow_comments:
            raise PermissionDenied("Comments are not allowed for this lesson.")
        serializer.save(user=self.request.user)


class LessonRatingViewSet(
    SoftDeleteMixin,
    DynamicSerializerMixin,
    FilteredLessonQuerysetMixin,
    viewsets.ModelViewSet
):
    """
    Allows users to rate lessons. Only one rating per user per lesson.
    """
    queryset = LessonRating.objects.select_related('lesson', 'user')
    serializer_class = LessonRatingSerializer
    write_serializer_class = LessonRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        lesson = serializer.validated_data.get('lesson')
        user = self.request.user

        if not lesson.allow_ratings:
            raise PermissionDenied("Ratings are not allowed for this lesson.")

        if LessonRating.objects.filter(lesson=lesson, user=user).exists():
            raise PermissionDenied("You have already rated this lesson.")

        serializer.save(user=user)

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can only edit your own rating.")
        serializer.save()
