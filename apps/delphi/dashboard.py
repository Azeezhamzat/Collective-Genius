from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from adhocracy4.dashboard import ModuleFormSetComponent
from adhocracy4.dashboard import components

from . import apps
from . import forms
from .models import Question


class QuestionsComponent(ModuleFormSetComponent):
    identifier = 'delphi_questions'
    weight = 20
    label = _('Questions')

    form_title = _('Edit Delphi questions')
    form_class = forms.QuestionFormSet
    form_template_name = 'a4_candy_delphi/includes/question_formset.html'

    def is_effective(self, module):
        module_app = module.phases[0].content().app
        return module_app == apps.Config.label

    def get_progress(self, module):
        if Question.objects.filter(module=module).exists():
            return 1, 1
        return 0, 1

    def get_base_url(self, module):
        return reverse(
            'a4dashboard:dashboard-delphi_questions-edit', kwargs={
                'organisation_slug': module.project.organisation.slug,
                'module_slug': module.slug,
            })


components.register_module(QuestionsComponent())
