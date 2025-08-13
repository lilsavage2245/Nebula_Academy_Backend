# dashboard/views/__init__.py
from .free import (
    FreeDashboardOverviewAPIView,
    FreeLessonStatsAPIView,
    FreeModulesView,
    ModuleLessonsDetailView,
)

__all__ = [
    "FreeDashboardOverviewAPIView",
    "FreeLessonStatsAPIView",
    "FreeModulesView",
    "ModuleLessonsDetailView",
]
