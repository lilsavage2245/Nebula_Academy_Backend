# event/urls.py
from django.urls import path, include
from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter

from .views import (
    EventCategoryViewSet,
    EventViewSet,
    SpeakerViewSet,
    EventSpeakerViewSet,
    EventRegistrationViewSet,
)

app_name = 'event'

# Root router
router = DefaultRouter()
router.register(r'categories', EventCategoryViewSet, basename='categories')
router.register(r'events', EventViewSet, basename='events')
router.register(r'speakers', SpeakerViewSet, basename='speakers')
router.register(r'event-speakers', EventSpeakerViewSet, basename='event-speakers')
router.register(r'registrations', EventRegistrationViewSet, basename='registrations')

# Nested router for event-scoped resources
# NOTE: lookup='event' -> nested kwarg is 'event_pk'
# If EventViewSet.lookup_field = 'slug', then 'event_pk' will contain the event's slug
event_router = NestedDefaultRouter(router, r'events', lookup='event')
event_router.register(r'speakers', EventSpeakerViewSet, basename='event-speakers-nested')
event_router.register(r'registrations', EventRegistrationViewSet, basename='event-registrations-nested')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(event_router.urls)),
]
