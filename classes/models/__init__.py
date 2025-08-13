# classes/models/__init__.py
from .lesson import Lesson, LessonMaterial
from .feedback import LessonComment, LessonReply, LessonRating
from .attendance import LessonAttendance
from .quiz import LessonQuiz, LessonQuizQuestion, LessonQuizResult, LessonQuizAnswer
from .enums import LessonAudience, MaterialAudience
from .base import SoftDeleteModelMixin

__all__ = [
    'Lesson', 'LessonMaterial',
    'LessonComment', 'LessonReply', 'LessonRating',
    'LessonAttendance',
    'LessonQuiz', 'LessonQuizQuestion', 'LessonQuizResult', 'LessonQuizAnswer',
    'LessonAudience', 'MaterialAudience',
    'SoftDeleteModelMixin',
]

