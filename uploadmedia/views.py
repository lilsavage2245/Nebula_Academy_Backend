# uploadmedia/views.py
import requests
from django.conf import settings
from rest_framework import views, permissions, status
from rest_framework.response import Response
from classes.models import Lesson  # adjust if your Lesson path differs
from .models import LessonVideo

class IsStaffUploader(permissions.BasePermission):
    def has_permission(self, request, view):
        u = request.user
        # while testing, you can relax this to IsAuthenticated only
        return bool(u and u.is_authenticated and getattr(u, "role", "").upper() in {"ADMIN","LECTURER","VOLUNTEER"})

class CreateDirectUploadView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsStaffUploader]

    def post(self, request, *args, **kwargs):
        lesson_id = request.data.get("lesson_id")
        if not lesson_id:
            return Response({"detail": "lesson_id required"}, status=400)

        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({"detail": "Lesson not found"}, status=404)

        allowed = [
            "localhost:3000",
            "127.0.0.1:3000",
            "staging.nebulacodeacademy.com",
            "api-staging.nebulacodeacademy.com",
        ]
        r = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{settings.CF_ACCOUNT_ID}/stream/direct_upload",
            headers={"Authorization": f"Bearer {settings.CF_STREAM_TOKEN}"},
            json={
                "maxDurationSeconds": 4 * 60 * 60,
                "creator": str(request.user.id),
                "allowedOrigins": allowed,           # hosts only, no protocol
                "thumbnailTimestampPct": 10,
            },
            timeout=30,
        )
        data = r.json()
        if not data.get("success"):
            return Response({"detail": "Cloudflare direct upload failed", "cf": data}, status=502)

        uid = data["result"]["uid"]
        upload_url = data["result"]["uploadURL"]

        # upsert the LessonVideo record
        video, _ = LessonVideo.objects.update_or_create(
            lesson=lesson,
            defaults={
                "provider": "CLOUDFLARE",
                "provider_id": uid,
                "status": "UPLOADING",
                "created_by": request.user,
            },
        )

        return Response({"upload_url": upload_url, "asset_uid": uid}, status=status.HTTP_201_CREATED)
