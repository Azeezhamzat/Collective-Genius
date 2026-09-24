from django.core.management.base import BaseCommand

from ...services import retry_due_deliveries


class Command(BaseCommand):
    help = ('Re-attempt any webhook deliveries whose retry time has '
           'passed. This project has no task queue/beat scheduler '
           'configured, so run this on a cron schedule (e.g. every few '
           'minutes) for retries to actually happen.')

    def handle(self, *args, **options):
        retry_due_deliveries()
        self.stdout.write(self.style.SUCCESS('Done.'))
