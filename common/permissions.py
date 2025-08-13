# common/permissions.py
from rest_framework import permissions


class IsAdminOnlyOrReadOnly(permissions.BasePermission):
    """
    Only admins can create/update/delete. Everyone else can read.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff


class IsAdminOrLecturerOrReadOnly(permissions.BasePermission):
    """
    Admins and lecturers can write. Everyone else can read.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated and
            (request.user.is_staff or getattr(request.user, 'role', '').upper() == 'LECTURER')
        )


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """
    Only the author of the object or admin can update/delete.
    Everyone else has read-only access.
    """

    def has_object_permission(self, request, view, obj):
        # Read-only requests allowed for anyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only author or admin can update/delete
        return request.user.is_authenticated and (
            obj.user == request.user or request.user.is_staff
        )

class IsLecturerOrVolunteerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(request.user, 'role', None) in ['LECTURER', 'VOLUNTEER']

class IsLecturerOrVolunteer(permissions.BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'role', None) in ['LECTURER', 'VOLUNTEER']

class IsStudentOrReadOnly(permissions.BasePermission):
    """
    Allows read-only for anyone, but write for authenticated ENROLLED students.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.is_authenticated and
            getattr(request.user, 'role', '').upper() == 'ENROLLED'
        )

class IsLessonAudienceAllowed(permissions.BasePermission):
    """
    Grants access based on the lesson's audience setting.
    Supports:
    - ALL: any authenticated user
    - ENROLLED: only users with role='ENROLLED'
    - LECTURER: only lecturers
    - FREE: only users with role='FREE'
    - BOTH: FREE or ENROLLED
    """

    def _is_user_allowed(self, user, audience):
        role = getattr(user, 'role', '').upper()
        audience = (audience or '').upper()

        if audience == 'ALL':
            return True
        elif audience == 'ENROLLED' and role == 'ENROLLED':
            return True
        elif audience == 'LECTURER' and role == 'LECTURER':
            return True
        elif audience == 'FREE' and role == 'FREE':
            return True
        elif audience == 'BOTH' and role in ['ENROLLED', 'FREE']:
            return True
        return False

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if not user.is_authenticated:
            return False

        from classes.models import Lesson, LessonQuiz

        quiz_id = (
            request.data.get('quiz') or
            view.kwargs.get('quiz_id') or
            view.kwargs.get('pk') or
            None
        )
        lesson_id = (
            request.data.get('lesson') or
            view.kwargs.get('lesson_id') or
            None
        )

        lesson = None
        try:
            if quiz_id:
                quiz = LessonQuiz.objects.select_related('lesson').get(pk=quiz_id)
                lesson = quiz.lesson
            elif lesson_id:
                lesson = Lesson.objects.get(pk=lesson_id)
        except (Lesson.DoesNotExist, LessonQuiz.DoesNotExist):
            return False

        if not lesson:
            return False

        return self._is_user_allowed(user, lesson.audience)

    def has_object_permission(self, request, view, obj):
        """
        Used in action methods with `@action(detail=True)` or manually called checks.
        Expects `obj` to be a LessonQuiz or Lesson.
        """
        from classes.models import LessonQuiz  # Local import to avoid circular dependency

        if isinstance(obj, LessonQuiz):
            return self._is_user_allowed(request.user, obj.lesson.audience)
        elif hasattr(obj, 'audience'):  # Covers Lesson or other lesson-like objects
            return self._is_user_allowed(request.user, obj.audience)

        return False
