# module/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Module
from achievement.models import Badge

@receiver(pre_save, sender=Module)
def auto_generate_module_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.title)

@receiver(post_save, sender=Module)
def auto_create_module_badge(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'badge'):
        Badge.objects.create(
            module=instance,
            name=f"{instance.title} Completion Badge",
            achievement_type='module_completion',
            xp_reward=100
        )
