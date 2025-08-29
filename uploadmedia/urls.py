# media/urls.py
from django.urls import path
from .views import CreateDirectUploadView
urlpatterns = [ path("videos/direct-upload", CreateDirectUploadView.as_view()) ]
