# core/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver, Signal
from django.utils.text import slugify
from common.utils import generate_unique_slug
from core.utils.email import send_verification_email
from .models import User

# ✅ Custom signal without providing_args
user_registered = Signal()

@receiver(pre_save, sender=User)
def user_slug_generator(sender, instance, *args, **kwargs):
    if not instance.slug:
        full_name = f"{instance.first_name} {instance.last_name}"
        instance.slug = generate_unique_slug(instance, full_name)

@receiver(user_registered)
def handle_user_registered(sender, user, request, **kwargs):
    """
    Send verification email when the custom user_registered signal is fired.
    """
    try:
        send_verification_email(user, request)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to send verification email: {e}")

@receiver(pre_save, sender=User)
def sync_category_from_level(sender, instance: User, **kwargs):
    """
    For ENROLLED users:
    - require program_level (DB constraint also enforces this)
    - keep program_category in sync with the level's program.category
    """
    if instance.role == User.Roles.ENROLLED and instance.program_level_id:
        instance.program_category = instance.program_level.program.category