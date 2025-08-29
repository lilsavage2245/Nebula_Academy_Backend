# uploadmedia/webhooks.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from classes.models import Lesson

class CloudflareStreamWebhook(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        secret = request.headers.get("X-CF-Webhook-Secret") or request.query_params.get("secret")
        if settings.CF_WEBHOOK_SECRET and secret != settings.CF_WEBHOOK_SECRET:
            return Response(status=status.HTTP_403_FORBIDDEN)

        event = (request.data.get("event") or request.data.get("type") or "").lower()
        video = request.data.get("video") or {}
        uid = request.data.get("uid") or video.get("uid")
        duration = video.get("duration")

        if not uid:
            return Response({"ok": True})

        try:
            lesson = Lesson.objects.get(video_provider="CLOUDFLARE", video_provider_id=uid)
        except Lesson.DoesNotExist:
            return Response({"ok": True})

        if event in ("video.ready", "ready"):
            lesson.video_status = "READY"
        elif event in ("error",):
            lesson.video_status = "ERROR"
        else:
            lesson.video_status = "PROCESSING"

        if duration:
            try:
                lesson.duration_minutes = float(duration) / 60.0
            except Exception:
                pass

        lesson.save(update_fields=["video_status", "duration_minutes"])
        return Response({"ok": True})
