from django.db.models.signals import pre_save
from django.dispatch import receiver
from common.utils import generate_unique_slug
from .models import Event

@receiver(pre_save, sender=Event)
def event_slug_generator(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = generate_unique_slug(instance, instance.title)
