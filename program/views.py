# programs/views.py
import logging
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Program, ProgramLevel, Session, Certificate, ProgramCategory
from .serializers import (
    ProgramSerializer,
    ProgramLevelSerializer,
    SessionSerializer,
    CertificateSerializer,
    ProgramCategorySerializer,
)

logger = logging.getLogger(__name__)

# --- Permissions ---
class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff


# --- Program ViewSet ---
class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.select_related('director').prefetch_related('levels', 'certificate')
    serializer_class = ProgramSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']

    @extend_schema(
        summary="List levels for this program",
        description="Returns all levels that belong to this program.",
        responses=ProgramLevelSerializer(many=True),
    )
    @action(detail=True, methods=['get'])
    def levels(self, request, slug=None):
        program = self.get_object()
        qs = (ProgramLevel.objects
              .filter(program=program)
              .select_related('program')
              .order_by('level_number'))

        # preserve pagination if you use DRF pagination globally
        page = self.paginate_queryset(qs)
        ser = ProgramLevelSerializer(page or qs, many=True, context={'request': request})
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    @extend_schema(
        summary="List sessions for this program",
        description="Returns all sessions across all levels of this program.",
        responses=SessionSerializer(many=True)
    )
    @action(detail=True, methods=['get'])
    def sessions(self, request, slug=None):
        program = self.get_object()
        qs = (Session.objects
              .filter(level__program=program)
              .select_related('level', 'level__program')
              .order_by('start_datetime'))
        page = self.paginate_queryset(qs)
        ser = SessionSerializer(page or qs, many=True, context={'request': request})
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)


# --- ProgramLevel ViewSet ---
class ProgramLevelViewSet(viewsets.ModelViewSet):
    queryset = ProgramLevel.objects.select_related('program')
    serializer_class = ProgramLevelSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering = ['level_number']

    def get_queryset(self):
        qs = super().get_queryset()

        # Try all plausible keys + query params
        rm = getattr(self.request, 'resolver_match', None)
        rm_kwargs = rm.kwargs if rm else {}
        program_slug = (
            self.kwargs.get('program_pk') or
            self.kwargs.get('program') or
            self.kwargs.get('slug') or
            rm_kwargs.get('program_pk') or
            rm_kwargs.get('program') or
            rm_kwargs.get('slug') or
            self.request.query_params.get('program') or
            self.request.query_params.get('program_slug')
        )

        logger.debug("ProgramLevelViewSet kwargs=%s rm.kwargs=%s program_slug=%s",
                     dict(self.kwargs), rm_kwargs, program_slug)

        if program_slug:
            qs = qs.filter(program__slug=program_slug)
        return qs

# --- Session ViewSet ---
class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.select_related('level', 'level__program')
    serializer_class = SessionSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'location', 'level__title', 'level__program__name']
    ordering_fields = ['start_datetime', 'end_datetime']
    ordering = ['start_datetime']

    def get_queryset(self):
        qs = super().get_queryset()

        rm = getattr(self.request, 'resolver_match', None)
        rm_kwargs = rm.kwargs if rm else {}
        program_slug = (
            self.kwargs.get('program_pk') or
            self.kwargs.get('program') or
            self.kwargs.get('slug') or
            rm_kwargs.get('program_pk') or
            rm_kwargs.get('program') or
            rm_kwargs.get('slug') or
            self.request.query_params.get('program') or
            self.request.query_params.get('program_slug')
        )
        level_id = (
            self.kwargs.get('level_pk') or
            rm_kwargs.get('level_pk') or
            self.request.query_params.get('level_id')
        )

        logging.getLogger(__name__).debug(
            "SessionViewSet kwargs=%s rm.kwargs=%s program_slug=%s level_id=%s",
            dict(self.kwargs), rm_kwargs, program_slug, level_id
        )

        if program_slug:
            qs = qs.filter(level__program__slug=program_slug)
        if level_id:
            qs = qs.filter(level_id=level_id)
        return qs



# --- Certificate ViewSet ---
class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.select_related('program')
    serializer_class = CertificateSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at']

    def get_queryset(self):
        program_slug = self.request.query_params.get('program')
        if program_slug:
            return self.queryset.filter(program__slug=program_slug)
        return self.queryset


# --- Public: Program Category List View ---
class ProgramCategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        data = ProgramCategorySerializer.from_enum()
        return Response(data)

