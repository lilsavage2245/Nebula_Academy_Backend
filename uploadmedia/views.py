# media/views.py
import requests
from django.conf import settings
from rest_framework import views, permissions, status
from rest_framework.response import Response
from classes.models import Lesson

class IsStaffUploader(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "role", "").upper() in {"ADMIN","LECTURER","VOLUNTEER"})

class CreateDirectUploadView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsStaffUploader]

    def post(self, request):
        lesson_id = request.data.get("lesson_id")
        if not lesson_id:
            return Response({"detail": "lesson_id required"}, status=400)
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({"detail": "Lesson not found"}, status=404)

        # allowedOrigins should list the *hosts* (no protocol)
        allowed = request.data.get("allowed_origins") or [
            "localhost:3000", "127.0.0.1:3000",
            "staging.nebulacodeacademy.com", "api-staging.nebulacodeacademy.com"
        ]

        r = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{settings.CF_ACCOUNT_ID}/stream/direct_upload",
            headers={"Authorization": f"Bearer {settings.CF_STREAM_TOKEN}"},
            json={
                "maxDurationSeconds": 4 * 60 * 60,
                "creator": str(request.user.id),
                "allowedOrigins": allowed,
                "thumbnailTimestampPct": 10
            },
            timeout=30
        )
        data = r.json()
        if not data.get("success"):
            return Response({"detail": "Cloudflare direct upload failed", "cf": data}, status=502)

        uid = data["result"]["uid"]
        upload_url = data["result"]["uploadURL"]

        lesson.video_provider = "CLOUDFLARE"
        lesson.video_provider_id = uid
        lesson.video_status = "UPLOADING"
        lesson.save(update_fields=["video_provider","video_provider_id","video_status"])

        return Response({"upload_url": upload_url, "asset_uid": uid}, status=status.HTTP_201_CREATED)
