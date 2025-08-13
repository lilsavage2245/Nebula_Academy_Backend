# classes/views/feedback.py
from rest_framework import viewsets, permissions, filters
from rest_framework.exceptions import PermissionDenied

from classes.models import LessonComment, LessonReply, LessonRating
from classes.serializers.feedback import (
    LessonCommentSerializer,
    LessonReplySerializer,
    LessonRatingSerializer
)
from .base import (
    SoftDeleteMixin,
    DynamicSerializerMixin,
    FilteredLessonQuerysetMixin
)


class LessonCommentViewSet(
    SoftDeleteMixin,
    DynamicSerializerMixin,
    FilteredLessonQuerysetMixin,
    viewsets.ModelViewSet
):
    """
    Allows users to comment on lessons. Comments are disabled per lesson setting.
    """
    queryset = LessonComment.objects.select_related('lesson', 'user').prefetch_related('replies')
    serializer_class = LessonCommentSerializer
    write_serializer_class = LessonCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        lesson = serializer.validated_data['lesson']
        if not lesson.allow_comments:
            raise PermissionDenied("Comments are not allowed for this lesson.")
        serializer.save(user=self.request.user)


class LessonReplyViewSet(
    SoftDeleteMixin,
    DynamicSerializerMixin,
    viewsets.ModelViewSet
):
    """
    Allows users to reply to lesson comments.
    """
    queryset = LessonReply.objects.select_related('parent_comment', 'user')
    serializer_class = LessonReplySerializer
    write_serializer_class = LessonReplySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def perform_create(self, serializer):
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
