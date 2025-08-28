# classes/serializers/__init__.py

# Re-export fields so consumers can use them without deep paths
from .fields import DisplayChoiceField, UserSafeField, TimeSinceField

# Re-export common mixins
from .base import TimestampedSerializerMixin, OwnedByUserMixin, IdSlugReadOnlyMixin

# Core serializers
from .lesson import (
    LessonSerializer,
    LessonCreateUpdateSerializer,
    LessonMaterialSerializer,
)

from .feedback import (
    LessonCommentSerializer,
    LessonRatingSerializer,
)

from .attendance import (
    LessonAttendanceSerializer,
    # Optionally expose a display-only summary if you created it:
    # LessonAttendanceSummarySerializer,
)

__all__ = [
    # fields
    "DisplayChoiceField", "UserSafeField", "TimeSinceField",
    # mixins
    "TimestampedSerializerMixin", "OwnedByUserMixin", "IdSlugReadOnlyMixin",
    # lesson
    "LessonSerializer", "LessonCreateUpdateSerializer", "LessonMaterialSerializer",
    # feedback
    "LessonCommentSerializer", "LessonRatingSerializer",
    # attendance
    "LessonAttendanceSerializer",
    # "LessonAttendanceSummarySerializer",
]
