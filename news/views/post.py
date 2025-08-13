from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from rest_framework.permissions import SAFE_METHODS
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend

from news.models import NewsPost
from news.serializers.post import (
    NewsPostSerializer,
    NewsPostCreateUpdateSerializer
)
from news.views.base import DynamicSerializerMixin, SoftDeleteMixin


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Only authors or admins can write. Everyone can read published content.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user and (obj.author == request.user or request.user.is_staff)


class NewsPostViewSet(
    SoftDeleteMixin,
    DynamicSerializerMixin,
    viewsets.ModelViewSet
):
    """
    Handles listing, creating, retrieving, updating, publishing, and soft-deleting news posts.
    """
    queryset = NewsPost.objects.select_related('author', 'category')
    serializer_class = NewsPostSerializer
    write_serializer_class = NewsPostCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['title', 'summary', 'content', 'tags']
    ordering_fields = ['published_on', 'created_at', 'view_count']
    ordering = ['-published_on', '-created_at']

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if self.action in ['list', 'retrieve']:
            return qs.filter(status='PUBLISHED', published_on__isnull=False)
        if user.is_staff:
            return qs
        return qs.filter(author=user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if (
            instance.status == NewsPost.Status.PUBLISHED and
            instance.published_on and
            instance.published_on <= timezone.now()
        ):
            instance.view_count = F('view_count') + 1
            instance.save(update_fields=['view_count'])
            instance.refresh_from_db(fields=['view_count'])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, slug=None):
        """
        Custom action: manually publish a post.
        """
        post = self.get_object()
        if post.status != NewsPost.Status.PUBLISHED:
            post.status = NewsPost.Status.PUBLISHED
            post.published_on = timezone.now()
            post.save(update_fields=['status', 'published_on'])
        return Response(self.get_serializer(post).data, status=status.HTTP_200_OK)
