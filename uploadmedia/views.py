# uploadmedia/views.py
import logging, requests, traceback
from django.conf import settings
from rest_framework import views, permissions, status
from rest_framework.response import Response
from classes.models import Lesson
from .models import LessonVideo  # the OneToOne we added

log = logging.getLogger(__name__)

class IsStaffUploader(permissions.BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, "role", "").upper() in {"ADMIN","LECTURER","VOLUNTEER"})

class CreateDirectUploadView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsStaffUploader]

    def post(self, request):
        try:
            lesson_id = request.data.get("lesson_id")
            if not lesson_id:
                return Response({"detail": "lesson_id required"}, status=400)

            # 1) Fetch lesson
            try:
                lesson = Lesson.objects.get(id=lesson_id)
            except Lesson.DoesNotExist:
                return Response({"detail": f"Lesson {lesson_id} not found"}, status=404)

            # 2) Ask Cloudflare for a direct upload URL
            allowed = [
                "localhost:3000",
                "127.0.0.1:3000",
                "staging.nebulacodeacademy.com",
                "api-staging.nebulacodeacademy.com",
            ]
            cf_headers = {"Authorization": f"Bearer {settings.CF_STREAM_TOKEN}"}
            payload = {
                "maxDurationSeconds": 4 * 60 * 60,
                "creator": str(request.user.id),
                "allowedOrigins": allowed,           # hosts only
                "thumbnailTimestampPct": 10,
            }
            r = requests.post(
                f"https://api.cloudflare.com/client/v4/accounts/{settings.CF_ACCOUNT_ID}/stream/direct_upload",
                headers=cf_headers, json=payload, timeout=30
            )
            data = r.json()
            if not data.get("success"):
                # return their error cleanly (no HTML page)
                return Response({"detail": "Cloudflare direct upload failed", "cf": data}, status=502)

            uid = data["result"]["uid"]
            upload_url = data["result"]["uploadURL"]

            # 3) Upsert LessonVideo (NO writes to Lesson fields that don’t exist)
            video, _ = LessonVideo.objects.update_or_create(
                lesson=lesson,
                defaults={
                    "provider": "CLOUDFLARE",
                    "provider_id": uid,
                    "status": "UPLOADING",
                    "created_by": request.user if request.user.is_authenticated else None,
                },
            )

            return Response({"upload_url": upload_url, "asset_uid": uid}, status=status.HTTP_201_CREATED)

        except Exception as e:
            log.exception("direct-upload failed")  # keep this
            import sys, traceback
            tb = "".join(traceback.format_exception(*sys.exc_info())[-3:])  # last 3 frames
            return Response(
                {"detail": "server_error", "error_type": type(e).__name__, "message": str(e), "where": tb},
                status=500,
            )
