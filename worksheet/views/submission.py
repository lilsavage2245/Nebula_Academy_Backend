from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from worksheet.models import WorksheetSubmission, Worksheet
from worksheet.serializers import (
    WorksheetSubmissionSerializer,
    WorksheetSubmissionCreateSerializer,
    WorksheetSubmissionReviewSerializer,
)
from worksheet.serializers.worksheet import WorksheetStaffSerializer
from common.permissions import IsLecturerOrVolunteer


class WorksheetSubmissionViewSet(viewsets.ModelViewSet):
    """
    Handles worksheet submission CRUD and review:
    - Supports both nested and flat routes
    - Students can create/view their own submissions
    - Lecturers/Volunteers can view and review all
    """
    queryset = WorksheetSubmission.objects.select_related('worksheet', 'user', 'reviewed_by')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['submitted_at', 'score']
    search_fields = ['worksheet__title', 'user__email']
    ordering = ['-submitted_at']

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset

        # ✅ Support nested routing by worksheet_slug
        worksheet_slug = self.kwargs.get('worksheet_slug')
        if worksheet_slug:
            qs = qs.filter(worksheet__slug=worksheet_slug)

        # ✅ Role-based access
        if user.is_staff or user.role in ['LECTURER', 'VOLUNTEER', 'GUEST']:
            return qs
        return qs.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return WorksheetSubmissionCreateSerializer
        elif self.action in ['review', 'partial_update', 'update']:
            return WorksheetSubmissionReviewSerializer
        elif self.request.user.is_staff or self.request.user.role in ['LECTURER', 'VOLUNTEER', 'GUEST']:
            return WorksheetStaffSerializer
        return WorksheetSubmissionSerializer

    def perform_create(self, serializer):
        worksheet_slug = self.kwargs.get('worksheet_slug')

        # ✅ If nested route, get worksheet from slug
        if worksheet_slug:
            worksheet = get_object_or_404(Worksheet, slug=worksheet_slug)
            serializer.save(user=self.request.user, worksheet=worksheet)
        else:
            serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsLecturerOrVolunteer])
    def review(self, request, pk=None):
        """
        Allows staff to review a submission.
        """
        submission = self.get_object()
        serializer = WorksheetSubmissionReviewSerializer(
            submission, data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def resubmit(self, request, pk=None):
        """
        Allows students to mark their submission as resubmitted.
        """
        submission = self.get_object()
        if submission.user != request.user:
            return Response(
                {"detail": "You can only resubmit your own submission."},
                status=status.HTTP_403_FORBIDDEN
            )
        submission.mark_resubmitted()
        return Response({"detail": "Resubmission successful."}, status=status.HTTP_200_OK)
