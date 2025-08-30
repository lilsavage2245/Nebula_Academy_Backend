# uploadmedia/models.py
from django.db import models
from django.conf import settings

class LessonVideo(models.Model):
    PROVIDERS = [
        ("CLOUDFLARE", "Cloudflare Stream"),
        ("YOUTUBE", "YouTube"),
        ("MUX", "Mux"),
        ("AWS", "AWS MediaConvert"),
    ]

    lesson = models.OneToOneField("classes.Lesson", on_delete=models.CASCADE, related_name="primary_video")

    provider = models.CharField(max_length=20, choices=PROVIDERS, default="CLOUDFLARE")
    provider_id = models.CharField(max_length=255, unique=True)  # Cloudflare UID
    status = models.CharField(max_length=32, default="UPLOADING")  # UPLOADING|PROCESSING|READY|ERROR

    # Useful metadata
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def hls_url(self) -> str:
        if self.provider == "CLOUDFLARE" and self.provider_id:
            return f"https://videodelivery.net/{self.provider_id}/manifest/video.m3u8"
        return ""

    def __str__(self):
        return f"{self.lesson.title} [{self.provider}:{self.provider_id}]"
