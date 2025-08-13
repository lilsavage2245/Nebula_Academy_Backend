# engagement/management/commands/prune_pings.py
from django.core.management.base import BaseCommand
from django.utils.timezone import now, timedelta
from engagement.models import EngagementPing

class Command(BaseCommand):
    help = "Delete engagement pings older than 90 days."

    def handle(self, *args, **opts):
        cutoff = now() - timedelta(days=90)
        deleted, _ = EngagementPing.objects.filter(minute__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} old pings"))
