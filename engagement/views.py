# engagement/views.py
from django.utils.timezone import now
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import timedelta

from engagement.models import EngagementPing

def _floor_to_minute(dt):
    return dt.replace(second=0, microsecond=0)

class EngagementPingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        client_ts = request.data.get("timestamp")  # optional ISO string from FE
        page = request.data.get("page") or ""
        meta = request.data.get("meta") or {}

        # Use server time for trust; optionally parse client_ts if you want
        minute = _floor_to_minute(now())

        try:
            EngagementPing.objects.create(user=user, minute=minute, page=page, meta=meta)
        except IntegrityError:
            # Already have a ping this minute → ignore (idempotent)
            pass

        return Response({"ok": True})

