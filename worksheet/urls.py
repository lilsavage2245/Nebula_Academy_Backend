# worksheet/urls.py
from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter
from worksheet.views.worksheet import WorksheetViewSet
from worksheet.views.submission import WorksheetSubmissionViewSet

router = DefaultRouter()
router.register(r'worksheets', WorksheetViewSet, basename='worksheet')

nested_router = NestedDefaultRouter(router, r'worksheets', lookup='worksheet')
nested_router.register(r'submissions', WorksheetSubmissionViewSet, basename='worksheet-submission')

urlpatterns = router.urls + nested_router.urls
