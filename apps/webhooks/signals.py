"""Wires a handful of real, high-value events across the platform to
webhook dispatch. Deliberately a small, clearly-justified starting set
(every one of these is a plain "a new X was created" post_save hook,
the simplest and least error-prone kind of trigger) rather than trying
to instrument every model change -- see docs/building_a_module.md for
how to add another event type.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from adhocracy4.reports.models import Report
from apps.consent.models import Proposal as ConsentProposal
from apps.forecasting.models import Question as ForecastingQuestion
from apps.synthesis.models import SynthesisSnapshot

from . import services


def _organisation_for_project(project):
    return project.organisation if project else None


@receiver(post_save, sender=Report)
def on_report_created(sender, instance, created, **kwargs):
    if not created:
        return
    organisation = _organisation_for_project(instance.project)
    if organisation is None:
        return
    services.dispatch_event(organisation, 'report.created', {
        'report_id': instance.pk,
        'description': instance.description,
    })


@receiver(post_save, sender=ConsentProposal)
def on_consent_proposal_created(sender, instance, created, **kwargs):
    if not created:
        return
    organisation = _organisation_for_project(instance.project)
    if organisation is None:
        return
    services.dispatch_event(organisation, 'consent_proposal.created', {
        'proposal_id': instance.pk,
        'title': instance.title,
        'module_id': instance.module_id,
    })


@receiver(post_save, sender=ForecastingQuestion)
def on_forecasting_question_created(sender, instance, created, **kwargs):
    if not created:
        return
    organisation = _organisation_for_project(instance.project)
    if organisation is None:
        return
    services.dispatch_event(organisation, 'forecasting_question.created', {
        'question_id': instance.pk,
        'title': instance.title,
        'module_id': instance.module_id,
    })


@receiver(post_save, sender=SynthesisSnapshot)
def on_synthesis_snapshot_created(sender, instance, created, **kwargs):
    if not created:
        return
    organisation = _organisation_for_project(instance.module.project)
    if organisation is None:
        return
    services.dispatch_event(organisation, 'synthesis_snapshot.created', {
        'snapshot_id': instance.pk,
        'module_id': instance.module_id,
        'n_participants': instance.n_participants,
    })
