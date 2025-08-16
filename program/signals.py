# program/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.apps import apps
from common.utils import generate_unique_slug
from .models import Program

@receiver(pre_save, sender=Program)
def program_slug_generator(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = generate_unique_slug(instance, instance.name)

@receiver(post_save, sender=Program)
def ensure_program_certificate_template(sender, instance: Program, created, **kwargs):
    if not created:
        return
    # Resolve models lazily via the app registry
    try:
        CertificateTemplate = apps.get_model('certificate', 'CertificateTemplate')
        CertificateType = apps.get_model('certificate', 'CertificateType')
    except LookupError:
        # certificate app not installed or not ready yet
        return

    # Create a default PROGRAM_COMPLETION template if none exists
    if not CertificateTemplate.objects.filter(
        program=instance,
        certificate_type=CertificateType.PROGRAM_COMPLETION
    ).exists():
        CertificateTemplate.objects.create(
            title=f"{instance.name} Completion",
            certificate_type=CertificateType.PROGRAM_COMPLETION,
            program=instance,
            criteria={"levels_required": "ALL"},
            layout_config={},
            is_active=True,
        )
