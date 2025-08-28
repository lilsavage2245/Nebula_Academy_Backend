# classes/models/__init__.py
from .lesson import Lesson, LessonMaterial
from .feedback import LessonComment, LessonRating
from .attendance import LessonAttendance
from .quiz import LessonQuiz, LessonQuizQuestion, LessonQuizResult, LessonQuizAnswer
from .enums import LessonAudience, MaterialAudience
from .base import SoftDeleteModelMixin

__all__ = [
    'Lesson', 'LessonMaterial',
    'LessonComment', 'LessonRating',
    'LessonAttendance',
    'LessonQuiz', 'LessonQuizQuestion', 'LessonQuizResult', 'LessonQuizAnswer',
    'LessonAudience', 'MaterialAudience',
    'SoftDeleteModelMixin',
]

