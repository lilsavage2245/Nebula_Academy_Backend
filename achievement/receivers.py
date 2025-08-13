# achievement/receivers.py

from django.dispatch import receiver
from achievement.signals import badge_awarded_signal
from achievement.models import BadgeAwardLog
import logging

logger = logging.getLogger(__name__)


@receiver(badge_awarded_signal)
def log_badge_award(sender, user, badge, **kwargs):
    """
    Called whenever a badge is awarded.
    Use this to log, create BadgeAwardLog, or trigger toast/notification.
    """
    BadgeAwardLog.objects.create(
        user=user,
        badge=badge,
        source="signal",
        reason="Awarded by evaluator",
        metadata={"source_badge": badge.slug}
    )

    logger.info(f"[Badge Awarded] {user.email} earned: {badge.name}")
