from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from adhocracy4.modules.models import Module

from ...services import run_synthesis


class Command(BaseCommand):
    help = ('Run the synthesis engine (opinion clustering + consensus '
           'scoring) for a module\'s comments and store a snapshot.')

    def add_arguments(self, parser):
        parser.add_argument('module_slug', type=str)
        parser.add_argument(
            '--min-votes', type=int, default=3,
            help='Minimum number of ratings a comment needs before it is '
                'included in the results (default: 3).')

    def handle(self, *args, **options):
        try:
            module = Module.objects.get(slug=options['module_slug'])
        except Module.DoesNotExist as err:
            raise CommandError(
                'No module with slug "{}"'.format(options['module_slug'])
            ) from err

        snapshot = run_synthesis(
            module, min_votes_per_statement=options['min_votes'])

        self.stdout.write(self.style.SUCCESS(
            'Synthesis run for "{}": {} participants, {} groups, '
            '{} statements scored.'.format(
                module, snapshot.n_participants, snapshot.n_groups,
                snapshot.statement_results.count())
        ))
