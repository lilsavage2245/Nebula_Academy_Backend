# program/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from common.utils import generate_unique_slug
from .models import Program, Certificate


@receiver(pre_save, sender=Program)
def program_slug_generator(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = generate_unique_slug(instance, instance.name)


@receiver(post_save, sender=Program)
def create_program_certificate(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'certificate'):
        Certificate.objects.create(
            program=instance,
            title=f"{instance.name} Completion Certificate",
            description=f"Certificate of completion for the {instance.name} program."
        )

