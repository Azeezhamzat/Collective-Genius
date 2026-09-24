from django.forms import inlineformset_factory

from adhocracy4.dashboard.components.forms import ModuleDashboardFormSet
from adhocracy4.modules import models as module_models

from .models import Question

QuestionFormSet = inlineformset_factory(
    module_models.Module, Question,
    fields=('title', 'description', 'scale_hint', 'current_round',
           'is_closed'),
    formset=ModuleDashboardFormSet,
    extra=3, can_delete=True,
)
