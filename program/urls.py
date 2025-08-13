# program/urls.py
from django.urls import path, include
from rest_framework_nested.routers import DefaultRouter, NestedSimpleRouter

from .views import (
    ProgramViewSet,
    ProgramLevelViewSet,
    SessionViewSet,
    CertificateViewSet,
    ProgramCategoryListView,
)

# Root router
router = DefaultRouter()
router.register(r'programs', ProgramViewSet, basename='program')
router.register(r'sessions', SessionViewSet, basename='session')  # optional flat route
router.register(r'certificates', CertificateViewSet, basename='certificate')

# Nested: levels under programs
program_router = NestedSimpleRouter(router, r'programs', lookup='program')
program_router.register(r'levels', ProgramLevelViewSet, basename='program-levels')

# Nested: sessions under programs (across all levels)
program_router.register(r'sessions', SessionViewSet, basename='program-sessions')

# Optional: sessions under levels
level_router = NestedSimpleRouter(program_router, r'levels', lookup='level')
level_router.register(r'sessions', SessionViewSet, basename='level-sessions')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(program_router.urls)),
    path('', include(level_router.urls)),
    path('program-categories/', ProgramCategoryListView.as_view(), name='program-category-list'),
]
