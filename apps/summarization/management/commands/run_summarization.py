from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from adhocracy4.modules.models import Module

from ...services import run_summarization


class Command(BaseCommand):
    help = ('Summarize a module\'s comments (extractive, top-N most '
           'representative) and store a snapshot.')

    def add_arguments(self, parser):
        parser.add_argument('module_slug', type=str)
        parser.add_argument('--top-n', type=int, default=5)
        parser.add_argument('--min-words', type=int, default=3)

    def handle(self, *args, **options):
        try:
            module = Module.objects.get(slug=options['module_slug'])
        except Module.DoesNotExist as err:
            raise CommandError(
                'No module with slug "{}"'.format(options['module_slug'])
            ) from err

        snapshot = run_summarization(
            module,
            top_n=options['top_n'],
            min_significant_words=options['min_words'],
        )

        self.stdout.write(self.style.SUCCESS(
            'Summarized "{}": {} comments, {} key comments picked, '
            'top keywords: {}'.format(
                module, snapshot.n_comments,
                snapshot.key_comments.count(),
                ', '.join(snapshot.keywords))
        ))
