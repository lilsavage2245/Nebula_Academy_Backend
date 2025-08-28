# module/views.py

from rest_framework import viewsets, permissions, filters, decorators, status
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied, NotFound
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from common.mixins import ModuleScopedQueryMixin
from common.pagination import SmallSetPagination, LargeSetPagination

from .models import (
    Module, ModuleLevelLink, ModuleLecturer,
    ModuleMaterial, EvaluationComponent,
    MaterialAudience
)

from .serializers import (
    ModuleSerializer, ModuleCreateUpdateSerializer,
    ModuleLevelLinkSerializer, ModuleLecturerSerializer,
    ModuleMaterialSerializer, ModuleMaterialCreateUpdateSerializer,
    EvaluationComponentSerializer,
)

from common.permissions import IsAdminOnlyOrReadOnly, IsAdminOrLecturerOrReadOnly

def user_can_access_material(user, material: ModuleMaterial) -> bool:
    """Gate by audience and your people roles."""
    # Anonymous users get nothing
    if not user or not user.is_authenticated:
        return False

    # Staff always allowed
    if getattr(user, "is_staff", False):
        return True

    audience = material.audience

    if audience == MaterialAudience.BOTH:
        return True

    if audience == MaterialAudience.FREE:
        # Allow FREE + ENROLLED (and any staff/lecturers)
        return getattr(user, "role", None) in ("FREE", "ENROLLED", "LECTURER", "STAFF")

    if audience == MaterialAudience.ENROLLED:
        # Only enrolled (and lecturers) should see
        return getattr(user, "role", None) in ("ENROLLED", "LECTURER", "STAFF")

    return False


# --- Module ViewSet ---
class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.prefetch_related(
        'modulelevellink_set__level',
        'modulelecturer_set__lecturer',
        'materials',
        'evaluations',
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

    def get_serializer_context(self):
        # Ensure we pass request for URL building (file_url, download_url)
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


# --- ModuleLevelLink ViewSet ---
class ModuleLevelLinkViewSet(ModuleScopedQueryMixin, viewsets.ModelViewSet):
    queryset = ModuleLevelLink.objects.select_related('module', 'level')
    serializer_class = ModuleLevelLinkSerializer
    permission_classes = [IsAdminOnlyOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order']

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


# --- ModuleLecturer ViewSet ---
class ModuleLecturerViewSet(ModuleScopedQueryMixin, viewsets.ModelViewSet):
    queryset = ModuleLecturer.objects.select_related('module', 'lecturer')
    serializer_class = ModuleLecturerSerializer
    permission_classes = [IsAdminOrLecturerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['lecturer__first_name', 'lecturer__last_name', 'lecturer__email']
    ordering_fields = ['role']

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

# --- ModuleMaterial ViewSet ---
class ModuleMaterialViewSet(ModuleScopedQueryMixin, viewsets.ModelViewSet):
    """
    Routes (assuming nested):
      GET/POST   /api/modules/<module_slug>/materials/
      GET/PATCH/DELETE /api/modules/<module_slug>/materials/<slug>/
      GET        /api/modules/<module_slug>/materials/<slug>/download/
    """
    lookup_field = "slug"
    permission_classes = [IsAdminOrLecturerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'version']
    ordering_fields = ['created_at', 'title', 'type', 'audience']
    pagination_class = SmallSetPagination

    def get_queryset(self):
        qs = ModuleMaterial.objects.select_related('module')
        module_slug = self.kwargs.get('module_slug')
        if module_slug:
            qs = qs.filter(module__slug=module_slug)
        return qs

    def get_object(self):
        module_slug = self.kwargs.get("module_slug")
        material_slug = self.kwargs.get(self.lookup_field)
        return get_object_or_404(
            ModuleMaterial.objects.select_related("module"),
            module__slug=module_slug, slug=material_slug
        )

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ModuleMaterialCreateUpdateSerializer
        return ModuleMaterialSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def perform_create(self, serializer):
        """
        Lecturers can only create for modules they are assigned to.
        Admin has full access.
        """
        module = self._get_module_from_request(serializer)
        user = self.request.user

        if getattr(user, "role", None) == 'LECTURER' and not module.modulelecturer_set.filter(lecturer=user).exists():
            raise PermissionDenied("You are not assigned to this module.")

        serializer.save(module=module)

    def perform_update(self, serializer):
        module = self._get_module_from_request(serializer, fallback_instance=self.get_object())
        user = self.request.user
        if getattr(user, "role", None) == 'LECTURER' and not module.modulelecturer_set.filter(lecturer=user).exists():
            raise PermissionDenied("You are not assigned to this module.")
        serializer.save(module=module)

    def _get_module_from_request(self, serializer, fallback_instance=None):
        """
        Resolve module from nested route; if not present, try instance.module.
        """
        module_slug = self.kwargs.get('module_slug')
        if module_slug:
            module = get_object_or_404(Module, slug=module_slug)
            return module
        if fallback_instance is not None:
            return fallback_instance.module
        # If someone tries to hit a non-nested route, require module explicitly
        mod = serializer.validated_data.get('module')
        if not mod:
            raise PermissionDenied("Module is required.")
        return mod

    @decorators.action(detail=True, methods=["get"], url_path="download",
                       permission_classes=[permissions.IsAuthenticated])
    def download(self, request, module_slug=None, slug=None):
        """
        Protected download/preview:
          - Enforces audience via user_can_access_material()
          - Streams file, or redirects to signed URL if storage supports it
        """
        material = self.get_object()

        if not user_can_access_material(request.user, material):
            raise PermissionDenied("You do not have access to this material.")

        if not material.file:
            # If it's an external link material, just redirect
            if material.external_url:
                return HttpResponseRedirect(material.external_url)
            raise NotFound("No file attached to this material.")

        # If your storage returns signed URLs (e.g., S3 via django-storages),
        # you can redirect instead of streaming:
        # try:
        #     signed_url = material.file.storage.url(material.file.name)
        #     return HttpResponseRedirect(signed_url)
        # except Exception:
        #     pass

        # Stream the file (browser can decide open vs download).
        filename = material.file.name.split("/")[-1]
        resp = FileResponse(material.file.open("rb"), filename=filename, as_attachment=False)
        # Set content type if you stored it (optional)
        if material.content_type:
            resp["Content-Type"] = material.content_type
        return resp


# --- EvaluationComponent ViewSet ---
class EvaluationComponentViewSet(ModuleScopedQueryMixin, viewsets.ModelViewSet):
    queryset = EvaluationComponent.objects.select_related('module')
    serializer_class = EvaluationComponentSerializer
    permission_classes = [IsAdminOrLecturerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['type', 'created_at']

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def perform_create(self, serializer):
        module = self._get_module()
        user = self.request.user
        if getattr(user, "role", None) == 'LECTURER' and not module.modulelecturer_set.filter(lecturer=user).exists():
            raise PermissionDenied("You are not assigned to this module.")
        serializer.save(module=module)

    def _get_module(self):
        module_slug = self.kwargs.get('module_slug')
        if not module_slug:
            raise PermissionDenied("Module slug required.")
        return get_object_or_404(Module, slug=module_slug)
