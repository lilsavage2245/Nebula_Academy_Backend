# achievement/services/evaluator.py

from django.utils.timezone import now
from django.db import transaction
from achievement.models import Badge, AwardedBadge, XPEvent, UserProfileAchievement, BadgeAwardLog
from achievement.signals.definitions import badge_awarded_signal

CRITERIA_FUNCTIONS = {
    "quizzes_passed": lambda user: __import__('classes.models.quiz', fromlist=['LessonQuizResult']).LessonQuizResult.objects.filter(user=user, passed=True).count(),
    "worksheets_submitted": lambda user: __import__('worksheet.models', fromlist=['WorksheetSubmission']).WorksheetSubmission.objects.filter(user=user).count(),
    "lessons_attended": lambda user: __import__('classes.models', fromlist=['LessonAttendance']).LessonAttendance.objects.filter(user=user, attended=True).count(),
    # Add more criteria keys as needed...
}

def user_has_badge(user, badge):
    return AwardedBadge.objects.filter(user=user, badge=badge).exists()


def meets_criteria(user, criteria: dict) -> bool:
    for key, required_value in criteria.items():
        count_func = CRITERIA_FUNCTIONS.get(key)
        if count_func is None:
            continue  # or raise ValueError(f"Unknown criteria key: {key}")
        if count_func(user) < required_value:
            return False
    return True


@transaction.atomic
def evaluate_badges_for_user(user):
    """
    Evaluates all active badges and awards any newly earned ones.
    Logs XP, emits signal, updates profile, and returns awarded list.
    """
    awarded_ids = AwardedBadge.objects.filter(user=user).values_list("badge_id", flat=True)
    candidate_badges = Badge.objects.filter(is_active=True, valid_from__lte=now()).exclude(id__in=awarded_ids)

    newly_awarded = []
    profile, _ = UserProfileAchievement.objects.get_or_create(user=user)

    for badge in candidate_badges:
        if badge.is_hidden:
            continue

        if meets_criteria(user, badge.criteria or {}):
            AwardedBadge.objects.create(user=user, badge=badge)
            newly_awarded.append(badge)

            # Log XP (optional)
            if badge.xp_reward:
                XPEvent.objects.create(
                    user=user,
                    xp=badge.xp_reward,
                    badge=badge,
                    action=f"Badge Earned: {badge.name}",
                    source=XPEvent.XPSourceType.SYSTEM
                )
                profile.total_xp += badge.xp_reward

            profile.update_level()
            profile.save(update_fields=["total_xp", "current_level", "last_updated"])

            # Log event
            BadgeAwardLog.objects.create(
                user=user,
                badge=badge,
                source="evaluator",
                reason="Auto-awarded by evaluator",
                metadata={"criteria": badge.criteria}
            )

            # Emit signal
            badge_awarded_signal.send(sender=Badge, user=user, badge=badge)

    return newly_awarded
