# programs/views.py
import logging
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import NotFound
from .utils import suggest_similar_level_slugs

from .models import Program, ProgramLevel, Session, ProgramCategory
from .serializers import (
    ProgramSerializer,
    ProgramLevelSerializer,
    SessionSerializer,
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
    queryset = Program.objects.select_related('director').prefetch_related('levels')
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
    queryset = ProgramLevel.objects.select_related('program').all()
    serializer_class = ProgramLevelSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # or your IsAdminOrReadOnly
    filter_backends = [filters.OrderingFilter]
    ordering = ['level_number']

    # 👇 tell DRF to resolve by slug, not pk
    lookup_field = 'slug'

    def get_queryset(self):
        qs = super().get_queryset()
        # Support filtering by parent program in nested routes:
        # /programs/{program_slug}/levels/...
        program_slug = self.kwargs.get('program_slug') or self.request.query_params.get('program')
        if program_slug:
            qs = qs.filter(program__slug=program_slug)
        return qs

    def get_object(self):
        """
        Override to provide a helpful 'did you mean ... ?' hint when slug is wrong.
        """
        # DRF will use lookup_field='slug' and kwarg '<lookup_field>'
        slug = self.kwargs.get(self.lookup_field)
        if slug is None:
            return super().get_object()

        try:
            return self.get_queryset().get(slug=slug)
        except ProgramLevel.DoesNotExist:
            program_slug = self.kwargs.get('program_slug')
            category = None
            if not program_slug:
                # If not nested by program, allow a broader hint by category param
                category = self.request.query_params.get('category')

            suggestions = suggest_similar_level_slugs(
                input_slug=slug,
                program_slug=program_slug,
                category=category,
                limit=5,
            )
            hint = ""
            if suggestions:
                hint = f" Did you mean: {', '.join(suggestions)}?"
            scope = f" for program '{program_slug}'" if program_slug else ""
            raise NotFound(detail=f"Program level with slug '{slug}' not found{scope}.{hint}")

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





# --- Public: Program Category List View ---
class ProgramCategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        data = ProgramCategorySerializer.from_enum()
        return Response(data)

