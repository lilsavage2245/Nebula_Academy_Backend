# engagement/urls.py
from django.urls import path
from engagement.views import EngagementPingView

urlpatterns = [
    path("ping/", EngagementPingView.as_view(), name="engagement-ping"),
]
