# module/urls.py
from django.urls import path, include
from rest_framework_nested.routers import DefaultRouter, NestedSimpleRouter

from .views import (
    ModuleViewSet,
    ModuleLevelLinkViewSet,
    ModuleLecturerViewSet,
    ModuleMaterialViewSet,
    EvaluationComponentViewSet,
)

app_name = "module"

# Root router
router = DefaultRouter()
router.register(r'modules', ModuleViewSet, basename='module')

# Nested router under modules
# NOTE: The nested kwarg will be "module_pk" (and it will contain the Module.slug value)
module_router = NestedSimpleRouter(router, r'modules', lookup='module')

module_router.register(r'levels', ModuleLevelLinkViewSet, basename='module-levels')
module_router.register(r'lecturers', ModuleLecturerViewSet, basename='module-lecturers')
module_router.register(r'materials', ModuleMaterialViewSet, basename='module-materials')
module_router.register(r'evaluations', EvaluationComponentViewSet, basename='module-evaluations')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(module_router.urls)),
]


