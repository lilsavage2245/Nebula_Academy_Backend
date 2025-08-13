# achievement/urls.py

from django.urls import path, include
from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter

from achievement.views.badge import BadgeViewSet, AwardedBadgeViewSet
from achievement.views.xp import XPEventViewSet
from achievement.views.profile import UserProfileAchievementView
from achievement.views.admin import UnearnedBadgesForUserView
from core.views import UserViewSet

# === Base router (users) ===
router = DefaultRouter()
router.register(r'badges', BadgeViewSet, basename='badge')
router.register(r'users', UserViewSet, basename='user')

# (Assumes user-related routes are handled by /api/users/)
# You can optionally mount this at /api/users/<user_id>/achievements/
user_router = NestedDefaultRouter(router, r'users', lookup='user')
user_router.register(r'awarded', AwardedBadgeViewSet, basename='user-awarded')
user_router.register(r'xp-events', XPEventViewSet, basename='user-xp-events')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(user_router.urls)),

    # Current user's profile achievement summary (non-nested)
    path('profile/', UserProfileAchievementView.as_view(), name='profile-achievement'),

    # Admin: view badges not earned by a specific user
    path('admin/unearned/', UnearnedBadgesForUserView.as_view(), name='admin-unearned-badges'),
]
