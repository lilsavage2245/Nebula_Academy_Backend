# uploadmedia/urls.py
from django.urls import path, re_path
from .views import CreateDirectUploadView
from .webhooks import CloudflareStreamWebhook
from .diag import CloudflareDiag

urlpatterns = [
    path("videos/direct-upload/", CreateDirectUploadView.as_view(), name="cf_direct_upload_slash"),
    re_path(r"^videos/direct-upload$", CreateDirectUploadView.as_view(), name="cf_direct_upload_no_slash"),
    path("webhooks/cloudflare/", CloudflareStreamWebhook.as_view(), name="cf_stream_webhook_slash"),
    re_path(r"^webhooks/cloudflare$", CloudflareStreamWebhook.as_view(), name="cf_stream_webhook_no_slash"),
    path("diag/cf/", CloudflareDiag.as_view()),
]
