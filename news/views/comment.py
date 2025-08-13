# news/views/comment.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from news.models import NewsComment
from news.serializers.comment import (
    NewsCommentSerializer,
    NewsCommentCreateSerializer,
    ReplySerializer,
    ReplyCreateSerializer
)
from news.views.base import DynamicSerializerMixin, SoftDeleteMixin
from common.permissions import IsAuthorOrAdminOrReadOnly


class NewsCommentViewSet(
    SoftDeleteMixin,
    DynamicSerializerMixin,
    viewsets.ModelViewSet
):
    """
    Handles CRUD for news comments.
    - Authenticated users can comment.
    - Only comment authors or admins can edit/delete.
    - Soft delete supported.
    - Public and other users only see approved comments.
    """
    queryset = NewsComment.objects.select_related('user', 'post', 'parent')
    serializer_class = NewsCommentSerializer
    write_serializer_class = NewsCommentCreateSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]
    lookup_field = 'id'

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if user.is_staff:
            return qs

        if user.is_authenticated:
            return qs.filter(is_deleted=False).filter(
                models.Q(is_approved=True) | models.Q(user=user)
            )

        return qs.filter(is_deleted=False, is_approved=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReplyViewSet(
    SoftDeleteMixin,
    DynamicSerializerMixin,
    viewsets.ModelViewSet
):
    """
    Handles reply creation and management.
    Enforces one-level nesting. Soft deletion supported.
    """
    queryset = NewsComment.objects.select_related('parent', 'post', 'user')
    serializer_class = ReplySerializer
    write_serializer_class = ReplyCreateSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]
    lookup_field = 'id'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(parent__isnull=False, is_deleted=False)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user and not request.user.is_staff:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
