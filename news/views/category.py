from rest_framework import viewsets, permissions
from news.models import NewsCategory
from news.serializers.category import NewsCategorySerializer


class NewsCategoryViewSet(viewsets.ModelViewSet):
    """
    - Public: list and retrieve categories
    - Staff: create, update, delete categories
    """
    queryset = NewsCategory.objects.all()
    serializer_class = NewsCategorySerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

