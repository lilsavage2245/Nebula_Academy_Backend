# uploadmedia/views.py
import logging, requests, traceback, sys
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
    permission_classes = [permissions.IsAuthenticated]  # keep role gate later

    def post(self, request):
        try:
            raw = request.data.get("lesson_id")
            try:
                lesson_id = int(raw)
            except (TypeError, ValueError):
                return Response({"detail": "lesson_id must be an integer"}, status=400)

            lesson = Lesson.objects.get(id=lesson_id)

            cf_headers = {"Authorization": f"Bearer {settings.CF_STREAM_TOKEN}"}
            
            # uploadmedia/views.py (when building payload)
            origin = request.headers.get("Origin") or ""
            # 'http://localhost:3000' => 'localhost:3000'
            this_host = origin.split("://")[-1] if "://" in origin else origin

            allowed = [
                "localhost:3000",
                "127.0.0.1:3000",
                "staging.nebulacodeacademy.com",
                "api-staging.nebulacodeacademy.com",
            ]
            if this_host and this_host not in allowed:
                allowed.append(this_host)  # dynamically allow current host:port


            payload = {
                "maxDurationSeconds": 4 * 60 * 60,
                "creator": str(request.user.id),
                "allowedOrigins": allowed,   # hosts only!
                "thumbnailTimestampPct": 0.1,  # <-- was 10
            }

            r = requests.post(
                f"https://api.cloudflare.com/client/v4/accounts/{settings.CF_ACCOUNT_ID}/stream/direct_upload",
                headers={**cf_headers},
                json=payload,
                timeout=30,
            )
            data = r.json()
            if not data.get("success"):
                return Response(
                    {
                        "detail": "cloudflare_error",
                        "status_code": r.status_code,
                        "errors": data.get("errors"),
                        "messages": data.get("messages"),
                    },
                    status=502,
                )

            uid = data["result"]["uid"]
            upload_url = data["result"]["uploadURL"]

            # ---- DB write (can be temporarily wrapped to not block uploads)
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

        except Lesson.DoesNotExist:
            return Response({"detail": f"Lesson {lesson_id} not found"}, status=404)
        except Exception as e:
            log.exception("direct-upload failed")
            tb = "".join(traceback.format_exception(*sys.exc_info())[-3:])
            # put everything inside `detail` so your client shows it
            return Response(
                {"detail": f"{type(e).__name__}: {e}", "where": tb},
                status=500
            )