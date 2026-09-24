from django.utils.translation import gettext_lazy as _

from adhocracy4 import phases

from . import apps
from . import models
from . import views


class ConsentPhase(phases.PhaseContent):
    app = apps.Config.label
    phase = 'consent'
    view = views.ProposalListDetail

    name = _('Consent decision phase')
    description = _(
        'Propose actions for the group, and decide by consent: a '
        'proposal passes once nobody has a standing objection to it.')
    module_name = _('consent decisions')

    features = {
        'crud': (models.Proposal,),
    }


phases.content.register(ConsentPhase())
