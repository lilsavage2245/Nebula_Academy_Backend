# event/urls.py
from django.urls import path, include
from rest_framework_nested.routers import DefaultRouter, NestedSimpleRouter

from .views import (
    EventCategoryViewSet,
    EventViewSet,
    SpeakerViewSet,
    EventSpeakerViewSet,
    EventRegistrationViewSet
)

app_name = 'event'

# Root router
router = DefaultRouter()
router.register(r'categories', EventCategoryViewSet, basename='category')
router.register(r'event', EventViewSet, basename='event')
router.register(r'speakers', SpeakerViewSet, basename='speaker')
router.register(r'event-speakers', EventSpeakerViewSet, basename='event-speaker')
router.register(r'registrations', EventRegistrationViewSet, basename='registration')

# Nested router for event-scoped resources
event_router = NestedSimpleRouter(router, r'event', lookup='event')
event_router.register(r'speakers', EventSpeakerViewSet, basename='event-speakers')
event_router.register(r'registrations', EventRegistrationViewSet, basename='event-registrations')

urlpatterns = [
    # Include all root-level routes
    path('', include(router.urls)),
    # Include nested event-specific routes
    path('', include(event_router.urls)),
]
