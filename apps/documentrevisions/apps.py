from django.apps import AppConfig


class Config(AppConfig):
    name = 'apps.documentrevisions'
    label = 'a4_candy_documentrevisions'

    def ready(self):
        from django.db.models.signals import pre_save

        from apps.documents.models import Paragraph

        from . import signals
        pre_save.connect(
            signals.snapshot_paragraph_revision, sender=Paragraph)
