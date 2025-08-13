# module/views.py

from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from common.mixins import ModuleScopedQueryMixin
from common.pagination import SmallSetPagination, LargeSetPagination
from .models import (
    Module, ModuleLevelLink, ModuleLecturer,
    LectureMaterial, EvaluationComponent
)
from achievement.models import Badge
from .serializers import (
    ModuleSerializer, ModuleCreateUpdateSerializer,
    ModuleLevelLinkSerializer, ModuleLecturerSerializer,
    LectureMaterialSerializer, EvaluationComponentSerializer,
    BadgeSerializer
)

# --- Permissions ---
from common.permissions import IsAdminOnlyOrReadOnly, IsAdminOrLecturerOrReadOnly

# --- Module ViewSet ---
class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.prefetch_related(
        'modulelevellink_set__level',
        'modulelecturer_set__lecturer',
        'materials',
        'evaluations',
        #'badge'
    )
    permission_classes = [IsAdminOnlyOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']
    ordering = ['title']
    lookup_field = 'slug'
    pagination_class = SmallSetPagination

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ModuleCreateUpdateSerializer
        return ModuleSerializer

# --- ModuleLevelLink ViewSet ---
class ModuleLevelLinkViewSet(ModuleScopedQueryMixin, viewsets.ModelViewSet):
    queryset = ModuleLevelLink.objects.select_related('module', 'level')
    serializer_class = ModuleLevelLinkSerializer
    permission_classes = [IsAdminOnlyOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order']


# --- ModuleLecturer ViewSet ---
class ModuleLecturerViewSet(ModuleScopedQueryMixin, viewsets.ModelViewSet):
    queryset = ModuleLecturer.objects.select_related('module', 'lecturer')
    serializer_class = ModuleLecturerSerializer
    permission_classes = [IsAdminOrLecturerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['lecturer__first_name', 'lecturer__last_name']
    ordering_fields = ['role']

# --- LectureMaterial ViewSet ---
class LectureMaterialViewSet(ModuleScopedQueryMixin, viewsets.ModelViewSet):
    queryset = LectureMaterial.objects.select_related('module')
    serializer_class = LectureMaterialSerializer
    permission_classes = [IsAdminOrLecturerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['created_at']

    def perform_create(self, serializer):
        module = serializer.validated_data['module']
        user = self.request.user

        if user.role == 'LECTURER' and not module.modulelecturer_set.filter(lecturer=user).exists():
            raise PermissionDenied("You are not assigned to this module.")
    
        serializer.save()


# --- EvaluationComponent ViewSet ---
class EvaluationComponentViewSet(ModuleScopedQueryMixin, viewsets.ModelViewSet):
    queryset = EvaluationComponent.objects.select_related('module')
    serializer_class = EvaluationComponentSerializer
    permission_classes = [IsAdminOrLecturerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['type', 'created_at']

    def perform_create(self, serializer):
        module = serializer.validated_data['module']
        user = self.request.user

        if user.role == 'LECTURER' and not module.modulelecturer_set.filter(lecturer=user).exists():
            raise PermissionDenied("You are not assigned to this module.")
    
        serializer.save()

# --- Badge ViewSet ---
class BadgeViewSet(ModuleScopedQueryMixin, viewsets.ModelViewSet):
    queryset = Badge.objects.select_related('module')
    serializer_class = BadgeSerializer
    permission_classes = [IsAdminOrLecturerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['created_at']
    pagination_class = LargeSetPagination

    def get_permissions(self):
        if self.request.method in ['POST', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [IsAdminOrLecturerOrReadOnly()]

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed("POST", detail="Badge creation is automated.")

