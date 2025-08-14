# core/utils/email.py
import logging
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from core.utils.urls import build_full_url
from django.core.mail import send_mail
from django.conf import settings
from email.utils import formataddr
from django.utils import timezone
from core.utils.request import get_client_ip


logger = logging.getLogger('core.email')
success_logger = logging.getLogger('core.email.success')

def _from_email():
    """
    Returns a proper 'From' value:
    - If DEFAULT_FROM_EMAIL already looks like 'Name <email>', return it.
    - Else, if EMAIL_SENDER_NAME is set, compose 'Name <email>'.
    - Else, fallback to 'Nebula Code Academy <DEFAULT_FROM_EMAIL>'.
    """
    default_from = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@localhost")
    # Already "Name <email>"? use as-is
    if "<" in default_from and ">" in default_from:
        return default_from
    # Prefer configured sender name; else use brand fallback
    sender_name = getattr(settings, "EMAIL_SENDER_NAME", "Nebula Code Academy")
    return formataddr((sender_name, default_from))



def send_verification_email(user, request):
    """
    Generate an email verification link for the given user and send it.

    Args:
        user: The user instance to verify.
        request: The current HTTP request, used to build an absolute URL.
    """
    # Create a one-time use token for email verification
    token = default_token_generator.make_token(user)
    # Encode the user's primary key
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    # Build the verification URL (expects a 'verify-email' named URL pattern)
    verification_path = reverse('verify-email')

    # 🌍 Domain logic: use settings first, fallback to request, else localhost
    domain = getattr(settings, "SITE_DOMAIN", None)
    if not domain and request:
        domain = request.get_host()
    if not domain:
        domain = "localhost:8000"  # fallback for dev/local testing

    scheme = "https" if not settings.DEBUG else "http"
    verification_url = build_full_url(request, f"{verification_path}?uid={uid}&token={token}")

    subject = 'Verify your Nebula Code Academy account'
    message = f"""Hello {user.first_name},

Thank you for registering at Nebula Code Academy. Please verify your email address by clicking the link below:

{verification_url}

If you did not register, please ignore this email.

— The Nebula Code Academy Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=_from_email(),  # ✅ robust sender
            recipient_list=[user.email],
            fail_silently=False,
        )
        success_logger.info(f"Verification email successfully sent to {user.email}")
    except Exception:
        logger.exception(f"Failed to send verification email to {user.email}")
        raise


def send_password_reset_email(user, request):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_path = reverse('password-reset-confirm')
    reset_url = build_full_url(request, f"{reset_path}?uid={uid}&token={token}")

    subject = "Reset your password - Nebula Code Academy"
    message = (
        f"Hi {user.first_name},\n\n"
        f"Use the link below to reset your password:\n{reset_url}\n\n"
        "If you didn't request this, please ignore.\n\n"
        "— NCA Team"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=_from_email(),  # ✅ robust sender
            recipient_list=[user.email],
            fail_silently=False,
        )
        success_logger.info(f"Password reset email successfully sent to {user.email}")
    except Exception:
        logger.exception(f"Failed to send password reset email to {user.email}")
        raise


def send_password_changed_notification(user, request=None):
    ip_info = ""
    if request:
        ip = get_client_ip(request)
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        ip_info = f"\n\nIP Address: {ip}\nTime: {timestamp}"

    subject = "Your Nebula Code Academy password was changed"
    message = (
        f"Hello {user.first_name},\n\n"
        "This is to notify you that your password was recently changed."
        f"{ip_info}\n\n"
        "If you did not authorize this change, please reset your password immediately or contact support.\n\n"
        "— The Nebula Code Academy Team"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=_from_email(),  # ✅ robust sender
            recipient_list=[user.email],
            fail_silently=False,
        )
        success_logger.info(f"[EMAIL SENT] Password change notification sent to {user.email}")
    except Exception:
        logger.exception(f"[EMAIL ERROR] Failed to send password change notification to {user.email}")