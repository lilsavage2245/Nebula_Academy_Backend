# classes/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include

from classes.views import (
    LessonViewSet,
    LessonMaterialViewSet,
    LessonCommentViewSet,
    LessonReplyViewSet,
    LessonRatingViewSet,
    LessonAttendanceViewSet,
)
from classes.views.quiz import (
    LessonQuizViewSet,
    LessonQuizQuestionViewSet,
    LessonQuizResultViewSet,
)

router = DefaultRouter()
router.register(r'lessons', LessonViewSet, basename='lessons')
router.register(r'materials', LessonMaterialViewSet, basename='materials')
router.register(r'comments', LessonCommentViewSet, basename='lesson-comments')
router.register(r'replies', LessonReplyViewSet, basename='lesson-replies')
router.register(r'ratings', LessonRatingViewSet, basename='lesson-ratings')
router.register(r'attendance', LessonAttendanceViewSet, basename='lesson-attendance')

router.register(r'quizzes', LessonQuizViewSet, basename='lesson-quiz')
router.register(r'quiz-questions', LessonQuizQuestionViewSet, basename='quiz-question')
router.register(r'quiz-results', LessonQuizResultViewSet, basename='quiz-result')

urlpatterns = [
    path('', include(router.urls)),
]
