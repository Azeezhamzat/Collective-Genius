from django.core.management.base import BaseCommand

from ...services import send_phase_deadline_reminders


class Command(BaseCommand):
    help = ('Notify followers of any project whose phase is ending '
           'within the next 24 hours and has not already been '
           'reminded about. Run this on a cron schedule (e.g. hourly) '
           '-- nothing calls it on its own.')

    def add_arguments(self, parser):
        parser.add_argument(
            '--window-hours', type=int, default=24,
            help='How far ahead to look for phases ending soon.')

    def handle(self, *args, **options):
        send_phase_deadline_reminders(window_hours=options['window_hours'])
        self.stdout.write(self.style.SUCCESS('Done.'))
