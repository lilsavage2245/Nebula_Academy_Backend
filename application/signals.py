# application/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Application, ApplicationStatus, ApplicationType

@receiver(post_save, sender=Application)
def handle_acceptance(sender, instance: Application, created, **kwargs):
    if created:
        return
    if instance.status != ApplicationStatus.ACCEPTED:
        return
    user = instance.applicant
    if not user:
        return

    # Enrolled student provisioning
    if instance.type == ApplicationType.PROGRAM:
        user.role = "ENROLLED"
        if instance.level_id:
            user.program_level_id = instance.level_id
            user.program_category = instance.level.program.category
        elif instance.program_id:
            user.program_category = instance.program.category
        user.is_active = True
        user.save(update_fields=["role", "program_level", "program_category", "is_active"])
