# achievement/views/profile.py

from rest_framework import generics, permissions
from achievement.models import UserProfileAchievement
from achievement.serializers.profile import UserProfileAchievementSerializer


class UserProfileAchievementView(generics.RetrieveAPIView):
    """
    Retrieve the current user's XP, level, and achievement profile.

    GET /api/achievements/profile/
    """
    serializer_class = UserProfileAchievementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = UserProfileAchievement.objects.get_or_create(user=self.request.user)
        return profile
