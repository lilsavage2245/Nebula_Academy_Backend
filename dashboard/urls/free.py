# dashboard/urls/free

from django.urls import path
from dashboard.views.free import (
    FreeDashboardOverviewAPIView,
    FreeLessonStatsAPIView,
    FreeModulesView,
    ModuleLessonsDetailView,
)
from badgetasks.views.task import WeeklyTaskListView


urlpatterns = [
    path('overview/', FreeDashboardOverviewAPIView.as_view(), name='free-dashboard-overview'),
    path('lesson-stats/', FreeLessonStatsAPIView.as_view(), name='free-lesson-stats'),
    path('modules/', FreeModulesView.as_view(), name='free-modules-view'),
    path('weekly-tasks/', WeeklyTaskListView.as_view(), name='weekly-task-list'),
]
