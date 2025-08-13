# news/views/subscriber.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from news.models import NewsSubscriber
from news.serializers.subscriber import (
    NewsSubscriberSerializer,
    NewsSubscriberCreateSerializer,
    NewsUnsubscribeSerializer
)
from news.views.base import DynamicSerializerMixin


class NewsSubscriberViewSet(DynamicSerializerMixin, viewsets.ModelViewSet):
    """
    Handles subscriptions to news categories or authors:
    - Users can subscribe to one at a time.
    - Only authenticated users can create or delete.
    - Read-only list of own subscriptions.
    """
    queryset = NewsSubscriber.objects.select_related('user', 'category', 'author')
    serializer_class = NewsSubscriberSerializer
    write_serializer_class = NewsSubscriberCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Always return only the subscriptions of the current user
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        read_serializer = NewsSubscriberSerializer(instance, context=self.get_serializer_context())
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='unsubscribe')
    def unsubscribe(self, request):
        """
        Custom endpoint to unsubscribe from a category or author.
        POST {"category_id": 1} or {"author_id": 2}
        """
        serializer = NewsUnsubscribeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)
