# achievement/views/admin.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model

from achievement.models import Badge, AwardedBadge
from achievement.serializers.badge import BadgeSerializer
from common.permissions import IsAdminOnlyOrReadOnly

User = get_user_model()


class UnearnedBadgesForUserView(APIView):
    """
    Admin-only view to return badges a user hasn't earned yet.

    Query Params:
    - user_id OR username (at least one is required)
    - include_hidden=true (optional, show hidden badges)
    - page, page_size for pagination
    """
    permission_classes = [IsAdminOnlyOrReadOnly]

    def get_user(self, request):
        user_id = request.query_params.get('user_id')
        username = request.query_params.get('username')

        if not user_id and not username:
            raise ValidationError({
                "user": "Provide either 'user_id' or 'username'."
            })

        try:
            if user_id:
                return User.objects.get(pk=user_id)
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise ValidationError({
                "user": "User not found."
            })

    def get(self, request):
        user = self.get_user(request)
        include_hidden = request.query_params.get('include_hidden') == 'true'

        awarded_ids = AwardedBadge.objects.filter(user=user).values_list('badge_id', flat=True)

        # Base queryset
        queryset = Badge.objects.filter(is_active=True).exclude(id__in=awarded_ids)

        # Optionally include hidden badges
        if not include_hidden:
            queryset = queryset.filter(is_hidden=False)

        # Paginate
        paginator = PageNumberPagination()
        paginated_qs = paginator.paginate_queryset(queryset, request)
        serializer = BadgeSerializer(paginated_qs, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
