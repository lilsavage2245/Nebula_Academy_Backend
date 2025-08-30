# uploadmedia/webhooks.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import LessonVideo

class CloudflareStreamWebhook(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        secret = request.headers.get("X-CF-Webhook-Secret") or request.query_params.get("secret")
        if settings.CF_WEBHOOK_SECRET and secret != settings.CF_WEBHOOK_SECRET:
            return Response(status=status.HTTP_403_FORBIDDEN)

        event = (request.data.get("event") or request.data.get("type") or "").lower()
        v = request.data.get("video") or {}
        uid = request.data.get("uid") or v.get("uid")
        duration = v.get("duration")

        if not uid:
            return Response({"ok": True})

        try:
            lv = LessonVideo.objects.select_related("lesson").get(provider="CLOUDFLARE", provider_id=uid)
        except LessonVideo.DoesNotExist:
            return Response({"ok": True})

        lv.status = "READY" if event in ("video.ready","ready") else ("ERROR" if event=="error" else "PROCESSING")
        if isinstance(duration, (int, float)) and duration > 0:
            lv.duration_seconds = int(duration)
            # keep your existing Lesson.duration_minutes in sync for analytics
            if hasattr(lv.lesson, "duration_minutes"):
                mins = max(1, round(duration/60.0))
                type(lv.lesson).objects.filter(pk=lv.lesson.pk).update(duration_minutes=mins)

        lv.save(update_fields=["status","duration_seconds"])
        return Response({"ok": True})
