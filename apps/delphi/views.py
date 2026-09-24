from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from adhocracy4.projects.mixins import DisplayProjectOrModuleMixin
from adhocracy4.projects.mixins import ProjectMixin

from . import services
from .models import Question
from .models import Response


class QuestionListDetail(ProjectMixin, DisplayProjectOrModuleMixin,
                         generic.View):
    """The module's main page for a Delphi phase: every question, with
    the previous rounds' anonymous aggregate + rationales, and a form
    to submit/revise an estimate for the current round.

    Registered as a phase view (see phases.py) -- same pattern as
    apps/quadraticvoting, apps/forecasting and apps/consent.
    """

    template_name = 'a4_candy_delphi/question_list.html'

    def get(self, request, *args, **kwargs):
        return self.render()

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse('account_login')
            return redirect('{}?next={}'.format(login_url, request.path))

        question = Question.objects.filter(
            module=self.module, pk=request.POST.get('question_id')).first()
        if question is None or question.is_closed:
            messages.error(request, _(
                'This question is not accepting responses.'))
            return self.render()

        try:
            value = float(request.POST.get('value', ''))
        except ValueError:
            messages.error(request, _('Please enter a number.'))
            return self.render()

        rationale = request.POST.get('rationale', '').strip()

        Response.objects.update_or_create(
            question=question, round_number=question.current_round,
            creator=request.user,
            defaults={'value': value, 'rationale': rationale},
        )
        messages.success(request, _('Your estimate was saved.'))
        return self.render()

    def render(self):
        return TemplateResponse(
            self.request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        questions = list(Question.objects.filter(module=self.module))

        for question in questions:
            history = services.round_history(question)
            # Previous rounds only -- the current round's own aggregate
            # isn't shown until it becomes a "previous" round, so nobody
            # is anchored by an in-progress round's partial results.
            # Once the question is closed there's no next round coming,
            # so the current round's results are final and shown too.
            if question.is_closed:
                question.previous_rounds = history
            else:
                question.previous_rounds = history[:-1] if history else []
            question.converged = services.has_converged(question)

            question.my_response = None
            if self.request.user.is_authenticated:
                question.my_response = Response.objects.filter(
                    question=question,
                    round_number=question.current_round,
                    creator=self.request.user,
                ).first()

            if question.previous_rounds:
                question.previous_rationales = list(
                    Response.objects.filter(
                        question=question,
                        round_number=question.current_round - 1,
                    ).exclude(rationale='').values_list(
                        'rationale', flat=True)
                )
            else:
                question.previous_rationales = []

        context['questions'] = questions
        return context
