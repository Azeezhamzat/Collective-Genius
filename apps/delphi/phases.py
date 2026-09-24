from django.utils.translation import gettext_lazy as _

from adhocracy4 import phases

from . import apps
from . import models
from . import views


class DelphiPhase(phases.PhaseContent):
    app = apps.Config.label
    phase = 'delphi'
    view = views.QuestionListDetail

    name = _('Delphi round phase')
    description = _(
        'Give an anonymous numeric estimate, see the group\'s '
        'aggregate, and revise it over structured rounds.')
    module_name = _('Delphi rounds')

    features = {
        'crud': (models.Response,),
    }


phases.content.register(DelphiPhase())
