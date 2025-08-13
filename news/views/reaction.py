# news/views/reaction.py
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from news.models import NewsReaction
from news.serializers.reaction import (
    NewsReactionSerializer,
    NewsReactionCreateUpdateSerializer
)
from news.views.base import DynamicSerializerMixin


class NewsReactionViewSet(DynamicSerializerMixin, viewsets.ModelViewSet):
    """
    Handles creation, update, and listing of reactions.
    - POST to toggle LIKE/DISLIKE.
    - Users can only react once per post (updated if already exists).
    - Public can view reaction counts.
    """
    queryset = NewsReaction.objects.select_related('user', 'post')
    serializer_class = NewsReactionSerializer
    write_serializer_class = NewsReactionCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        post_id = self.request.query_params.get('post')
    
        if self.action == 'mine':
            return qs.filter(user=self.request.user)

        if post_id:
            return qs.filter(post__id=post_id)
    
        return qs.none()


    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        headers = self.get_success_headers(serializer.data)

        # Determine if this was an update or create
        updated = serializer.context.get('updated', False)
        status_code = status.HTTP_200_OK if updated else status.HTTP_201_CREATED

        display_serializer = NewsReactionSerializer(instance, context=self.get_serializer_context())
        return Response(display_serializer.data, status=status_code, headers=headers)
    
    def perform_destroy(self, instance):
        if self.request.user != instance.user and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own reaction.")
        instance.delete()


    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def mine(self, request):
        """
        List current user's reactions.
        """
        queryset = self.get_queryset().filter(user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
