from django.utils.translation import gettext_lazy as _

from adhocracy4 import phases

from . import apps
from . import models
from . import views


class ForecastPhase(phases.PhaseContent):
    app = apps.Config.label
    phase = 'forecast'
    view = views.QuestionListDetail

    name = _('Forecasting phase')
    description = _(
        'Forecast the probability of each question\'s outcome.')
    module_name = _('forecasting')

    features = {
        'crud': (models.Forecast,),
    }


phases.content.register(ForecastPhase())
