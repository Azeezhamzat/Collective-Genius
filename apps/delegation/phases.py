from django.utils.translation import gettext_lazy as _

from adhocracy4 import phases

from . import apps
from . import models
from . import views


class DelegationPhase(phases.PhaseContent):
    app = apps.Config.label
    phase = 'delegation'
    view = views.DelegationRoundDetail

    name = _('Liquid democracy phase')
    description = _(
        'Vote directly, or delegate your vote to someone you trust -- '
        'who can delegate onward in turn. A vote can be recast or '
        'un-delegated at any time while the round is open.')
    module_name = _('liquid democracy')

    features = {
        'crud': (models.Vote, models.Delegation),
    }


phases.content.register(DelegationPhase())
