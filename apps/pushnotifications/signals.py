"""Wires the same 'a synthesis run completed' event
apps/webhooks/signals.py already hooks into a push notification to
that project's followers. Deliberately just this one event to start --
see docs/building_a_module.md for how to add another.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.synthesis.models import SynthesisSnapshot

from . import services


@receiver(post_save, sender=SynthesisSnapshot)
def on_synthesis_snapshot_created(sender, instance, created, **kwargs):
    if not created:
        return
    project = instance.module.project
    services.notify_project_followers(
        project, 'synthesis_snapshot.created',
        title='New synthesis results',
        body='A synthesis run completed for {}.'.format(project.name),
        url=project.get_absolute_url(),
    )
