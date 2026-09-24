from django.utils.translation import gettext_lazy as _

from adhocracy4 import phases

from . import apps
from . import models
from . import views


class VotingPhase(phases.PhaseContent):
    app = apps.Config.label
    phase = 'voting'
    view = views.VotingRoundDetail

    name = _('Quadratic voting phase')
    description = _(
        'Spend voice credits across options to express how strongly you '
        'feel, not just which one you prefer.')
    module_name = _('quadratic voting')

    features = {
        'crud': (models.Allocation,),
    }


phases.content.register(VotingPhase())
