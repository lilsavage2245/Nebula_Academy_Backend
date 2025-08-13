# achievemens/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

from worksheet.models import WorksheetSubmission
from classes.models.quiz import LessonQuizResult
from classes.models import LessonAttendance
from achievement.models import XPEvent, BadgeAwardLog
from achievement.services.evaluator import evaluate_badges_for_user
from achievement.signals.definitions import badge_awarded_signal  # Import the signal

# 🚀 Signal handlers for XP and badge evaluation

@receiver(post_save, sender=WorksheetSubmission)
def handle_worksheet_submission(sender, instance, created, **kwargs):
    if created:
        XPEvent.objects.create(
            user=instance.user,
            action="Worksheet submitted",
            xp=5,
            related_object={"worksheet_id": instance.worksheet.id},
            source=XPEvent.XPSourceType.ACTION
        )
        evaluate_badges_for_user(instance.user)


@receiver(post_save, sender=LessonQuizResult)
def handle_quiz_result(sender, instance, created, **kwargs):
    if created and instance.passed:
        XPEvent.objects.create(
            user=instance.user,
            action="Quiz passed",
            xp=10,
            related_object={"quiz_id": instance.quiz.id},
            source=XPEvent.XPSourceType.ACTION
        )
        evaluate_badges_for_user(instance.user)


@receiver(post_save, sender=LessonAttendance)
def handle_lesson_attendance(sender, instance, created, **kwargs):
    if created:
        XPEvent.objects.create(
            user=instance.user,
            action="Class attended",
            xp=8,
            related_object={"lesson_id": instance.lesson.id},
            source=XPEvent.XPSourceType.ACTION
        )
        evaluate_badges_for_user(instance.user)


@receiver(badge_awarded_signal)
def handle_badge_awarded(sender, user, badge, source=None, **kwargs):
    # Log to BadgeAwardLog
    BadgeAwardLog.objects.create(user=user, badge=badge, source=source)

    # Optional: Toast or in-app notification
    print(f"[🏅 Badge Awarded] {user.email} earned: {badge.name}")
