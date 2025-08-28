# classes/views/lesson.py

import boto3
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from rest_framework.decorators import action
from rest_framework import viewsets, filters
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from classes.models import Lesson, LessonMaterial
from classes.serializers.lesson import (
    LessonSerializer,
    LessonCreateUpdateSerializer,
    LessonMaterialSerializer
)
from .base import (
    SoftDeleteMixin,
    DynamicSerializerMixin,
    FilteredLessonQuerysetMixin
)
from common.permissions import IsAdminOnlyOrReadOnly, IsAdminOrLecturerOrReadOnly, IsLecturerOrVolunteerOrReadOnly  # assumes custom perms


class LessonViewSet(
    SoftDeleteMixin,
    DynamicSerializerMixin,
    FilteredLessonQuerysetMixin,
    viewsets.ModelViewSet
):
    """
    Lesson CRUD – staff can create/edit, students can view.
    """
    queryset = Lesson.objects.filter(is_active=True).select_related(
        'program_level', 'module', 'session'
    ).prefetch_related('materials', 'comments', 'ratings')
    permission_classes = [IsAdminOrLecturerOrReadOnly, IsLecturerOrVolunteerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # <-- allow file + JSON
    serializer_class = LessonSerializer
    write_serializer_class = LessonCreateUpdateSerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'created_at', 'title']
    ordering = ['-date']


class LessonMaterialViewSet(
    SoftDeleteMixin,
    DynamicSerializerMixin,
    viewsets.ModelViewSet
):
    """
    Materials upload/update. Only allowed if user is staff or lecturer.
    """
    queryset = LessonMaterial.objects.filter(is_active=True).select_related('lesson', 'uploaded_by')
    serializer_class = LessonMaterialSerializer
    permission_classes = [IsAdminOrLecturerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['created_at', 'version']
    ordering = ['-created_at']

    def _check_material_access(self, request, obj: LessonMaterial):
        # Reuse your lesson audience logic; you can extend with per-material audience
        # For simple case, treat material.audience like lesson audience:
        user = request.user
        # If you have a dedicated MaterialAudience checker, use it; else reuse lesson one:
        if obj.audience == 'BOTH' and getattr(user, 'role', '').upper() in ('FREE', 'ENROLLED'):
            return True
        if obj.audience == 'FREE' and getattr(user, 'role', '').upper() == 'FREE':
            return True
        if obj.audience == 'ENROLLED' and getattr(user, 'role', '').upper() == 'ENROLLED':
            return True
        if obj.audience == 'STAFF' and (user.is_staff or getattr(user, 'role', '').upper() == 'LECTURER'):
            return True
        # Fall back to lesson-level audience if you prefer:
        # return IsLessonAudienceAllowed().has_object_permission(request, self, obj.lesson)
        raise PermissionDenied("You are not allowed to access this material.")

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """
        Secure download endpoint.
        - For file uploads:
            * S3: presign and redirect
            * Local dev: stream or use X-Accel-Redirect if behind Nginx
        - For external URLs: redirect directly
        """
        obj = self.get_object()
        self._check_material_access(request, obj)

        # External link: just redirect
        if obj.url and not obj.file:
            return HttpResponseRedirect(obj.url)

        if not obj.file:
            raise NotFound("No file or URL available for this material.")

        # Determine content type (optional)
        guessed_type, _ = mimetypes.guess_type(obj.file.name)
        content_type = guessed_type or 'application/octet-stream'
        filename = obj.title or obj.file.name.split('/')[-1]

        # S3 backend
        if settings.STORAGE_BACKEND == "s3":
            s3_client = boto3.client(
                's3',
                region_name=getattr(settings, "AWS_S3_REGION_NAME", None),
                endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL", None),
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            bucket = settings.AWS_STORAGE_BUCKET_NAME
            key = obj.file.name  # path in the bucket

            # short-lived presigned URL (e.g., 60 seconds)
            url = s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': bucket,
                    'Key': key,
                    'ResponseContentType': content_type,
                    'ResponseContentDisposition': f'attachment; filename="{filename}"',
                },
                ExpiresIn=60,
            )
            return HttpResponseRedirect(url)

        # Local dev: stream file (simple) OR use X-Accel-Redirect (better under Nginx)
        # Simple stream (OK for dev, not ideal for big files):
        response = HttpResponse(obj.file.open('rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        lesson_slug = self.kwargs.get('lesson_slug') or self.request.query_params.get('lesson')
        if lesson_slug:
            qs = qs.filter(lesson__slug=lesson_slug)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        lesson = serializer.validated_data.get('lesson')

        # Allow only staff, session director, or assigned lecturers
        if not user.is_staff:
            if lesson.session and hasattr(lesson.session, 'director'):
                if user == lesson.session.director:
                    pass
                elif lesson.module.modulelecturer_set.filter(lecturer=user).exists():
                    pass
                else:
                    raise PermissionDenied("You do not have permission to upload materials for this lesson.")
            else:
                raise PermissionDenied("You do not have permission to upload materials.")
        
        serializer.save(uploaded_by=user)
