from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from adhocracy4.projects.mixins import DisplayProjectOrModuleMixin
from adhocracy4.projects.mixins import ProjectMixin

from . import services
from .models import Forecast
from .models import Question


class QuestionListDetail(ProjectMixin, DisplayProjectOrModuleMixin,
                         generic.View):
    """The module's main page for a forecasting phase: every question,
    each with a form to submit/update a forecast (while forecasting is
    open) or the resolved outcome plus the crowd's aggregate forecast
    (once resolved).

    Registered as a phase view (see phases.py) -- reached through the
    module's own canonical URL, same pattern as apps/quadraticvoting.
    """

    template_name = 'a4_candy_forecasting/question_list.html'

    def get(self, request, *args, **kwargs):
        return self.render()

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse('account_login')
            return redirect('{}?next={}'.format(login_url, request.path))

        question = Question.objects.filter(
            module=self.module, pk=request.POST.get('question_id')).first()
        if question is None:
            return self.render()

        if question.is_resolved:
            messages.error(request, _(
                'This question has already been resolved; forecasts '
                'are closed.'))
            return self.render()

        try:
            probability = int(request.POST.get('probability', ''))
        except ValueError:
            messages.error(request, _('Please enter a whole number '
                                      'percentage.'))
            return self.render()

        if not 0 <= probability <= 100:
            messages.error(request, _(
                'Probability must be between 0 and 100.'))
            return self.render()

        Forecast.objects.update_or_create(
            question=question, creator=request.user,
            defaults={'probability': probability},
        )
        messages.success(request, _('Your forecast was saved.'))
        return self.render()

    def render(self):
        return TemplateResponse(
            self.request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        questions = list(
            Question.objects.filter(module=self.module))

        my_forecasts = {}
        if self.request.user.is_authenticated:
            my_forecasts = {
                f.question_id: f.probability
                for f in Forecast.objects.filter(
                    question__in=questions, creator=self.request.user)
            }

        for question in questions:
            question.my_probability = my_forecasts.get(question.pk)
            if question.is_resolved:
                aggregate = services.aggregate_for_question(question)
                question.aggregate_percent = (
                    round(aggregate * 100) if aggregate is not None
                    else None)

        context['questions'] = questions

        leaderboard = services.leaderboard_for_module(self.module)
        users_by_id = get_user_model().objects.in_bulk(
            [int(entry.forecaster_id) for entry in leaderboard])
        for entry in leaderboard:
            entry.forecaster = users_by_id.get(int(entry.forecaster_id))
            entry.calibration_percent = round(
                (1 - entry.mean_brier_score) * 100)
        context['leaderboard'] = leaderboard

        return context
