# classes/models/attendance.py
from django.db import models
from django.conf import settings
from .lesson import Lesson

class LessonAttendance(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_attendances')

    attended_live = models.BooleanField(default=False)
    attended_replay = models.BooleanField(default=False)
    attended = models.BooleanField(default=False)  # This becomes computed

    watched_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Percent of video watched (0 - 100)"
    )
    duration = models.PositiveIntegerField(
        default=0,
        help_text="Total minutes spent watching the lesson"
    )

    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('lesson', 'user')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.get_full_name()} - {'Attended' if self.attended else 'Not Yet'} {self.lesson.title}"

    def update_attendance(self):
        self.attended = self.attended_live or self.attended_replay
        self.save(update_fields=["attended", "timestamp"])
