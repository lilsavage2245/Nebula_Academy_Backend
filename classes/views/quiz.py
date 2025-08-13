# classes/views/quiz
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import math


from classes.models import LessonQuiz, LessonQuizQuestion, LessonQuizResult, LessonQuizAnswer

from classes.serializers.quiz import (
    LessonQuizSerializer,
    LessonQuizCreateUpdateSerializer,
    LessonQuizQuestionSerializer,
    LessonQuizQuestionCreateSerializer,
    LessonQuizResultSerializer,
    LessonQuizResultSubmitSerializer
)

from .base import DynamicSerializerMixin
from common.permissions import IsAdminOrLecturerOrReadOnly, IsLecturerOrVolunteerOrReadOnly, IsLessonAudienceAllowed


class LessonQuizViewSet(DynamicSerializerMixin, viewsets.ModelViewSet):
    """
    Handles quizzes linked to lessons.
    - Students: list available quizzes (GET)
    - Admins/Lecturers: can create/edit (POST/PUT/DELETE)
    """
    queryset = LessonQuiz.objects.select_related('lesson')
    serializer_class = LessonQuizSerializer
    write_serializer_class = LessonQuizCreateUpdateSerializer
    permission_classes = [IsAdminOrLecturerOrReadOnly, IsLecturerOrVolunteerOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_staff and getattr(user, 'role', '').upper() != 'LECTURER':
            raise PermissionDenied("Only staff or lecturers can create quizzes.")
        serializer.save()

    def perform_update(self, serializer):
        self.perform_create(serializer)  # Same logic


class LessonQuizQuestionViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD for quiz questions.
    - Admins and lecturers can manage.
    - Everyone can read.
    """
    queryset = LessonQuizQuestion.objects.select_related('quiz')
    serializer_class = LessonQuizQuestionSerializer
    permission_classes = [IsAdminOrLecturerOrReadOnly]


class LessonQuizResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Students can view their own results.
    Admins can view all results.
    """
    serializer_class = LessonQuizResultSerializer
    permission_classes = [IsLessonAudienceAllowed]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return LessonQuizResult.objects.all().select_related('quiz', 'user').prefetch_related('answers')
        return LessonQuizResult.objects.filter(user=user).select_related('quiz').prefetch_related('answers')


    @action(detail=True, methods=['post'], url_path='submit', url_name='submit')
    def submit(self, request, pk=None):
        """
        Submit answers for a quiz.
        Payload:
        {
            "answers": [
                {"question_id": 1, "selected_answer": "A"},
                ...
            ]
        }
        """
        user = request.user
        quiz = get_object_or_404(LessonQuiz, pk=pk)

        print(f"🔎 SUBMISSION ATTEMPT BY: {user.email} (role={user.role})")
        print(f"🎯 QUIZ ID: {quiz.id} | Lesson Audience: {quiz.lesson.audience}")

        # Check audience permission
        permission = IsLessonAudienceAllowed()
        if not permission.has_object_permission(request, self, quiz):
            print(f"User role: {user.role}, Lesson audience: {quiz.lesson.audience}")
            return Response({"detail": "You are not allowed to take this quiz."}, status=403)


        if not quiz.is_active:
            return Response({"detail": "This quiz is not currently active."}, status=400)

        if LessonQuizResult.objects.filter(user=user, quiz=quiz).exists():
            return Response({"detail": "You have already submitted this quiz."}, status=409)

        answers_data = request.data.get("answers", [])
        if not answers_data:
            raise ValidationError("No answers submitted.")

        questions = {q.id: q for q in quiz.questions.all()}
        total_questions = len(questions)
        correct = 0

        result = LessonQuizResult.objects.create(user=user, quiz=quiz)

        for item in answers_data:
            qid = item.get("question_id")
            selected = item.get("selected_answer")
            question = questions.get(qid)

            if not question:
                continue

            is_correct = question.correct_answer == selected
            if is_correct:
                correct += 1

            LessonQuizAnswer.objects.create(
                result=result,
                question=question,
                selected_answer=selected,
                is_correct=is_correct
            )

        result.score = correct
        PASS_PERCENT = 70
        required = math.ceil((PASS_PERCENT / 100) * total_questions)
        result.passed = correct >= required
        result.save()

        return Response(self.get_serializer(result).data, status=201)


