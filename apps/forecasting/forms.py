from django.forms import inlineformset_factory

from adhocracy4.dashboard.components.forms import ModuleDashboardFormSet
from adhocracy4.modules import models as module_models

from .models import Question

QuestionFormSet = inlineformset_factory(
    module_models.Module, Question,
    fields=('title', 'resolution_criteria', 'closes_at', 'is_resolved',
           'outcome'),
    formset=ModuleDashboardFormSet,
    extra=3, can_delete=True,
)
