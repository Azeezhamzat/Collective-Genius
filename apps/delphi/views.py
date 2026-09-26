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


def _convergence_chart(rounds):
    """SVG-ready coordinates (0-100 viewBox) for a round-over-round
    convergence chart: a min/max band plus a median line, one point per
    round. Returns None if there are fewer than two rounds with data to
    plot a line between.
    """
    rounds = [r for r in rounds if r is not None]
    if len(rounds) < 2:
        return None

    global_min = min(r.minimum for r in rounds)
    global_max = max(r.maximum for r in rounds)
    value_range = (global_max - global_min) or 1

    def y_for(value):
        # SVG y grows downward; flip so higher values sit higher on screen.
        return round(100 - (value - global_min) / value_range * 100, 1)

    n = len(rounds)

    def x_for(i):
        return round(i / (n - 1) * 100, 1) if n > 1 else 50.0

    band_top = [(x_for(i), y_for(r.maximum)) for i, r in enumerate(rounds)]
    band_bottom = [(x_for(i), y_for(r.minimum))
                   for i, r in enumerate(rounds)]
    band_points = band_top + list(reversed(band_bottom))

    markers = []
    for i, r in enumerate(rounds):
        markers.append({
            'x': x_for(i),
            'y': y_for(r.median),
            'round_number': r.round_number,
            'median': r.median,
            'is_first': i == 0,
            'is_last': i == n - 1,
        })

    return {
        'band_points': ' '.join(
            '{},{}'.format(x, y) for x, y in band_points),
        'line_points': ' '.join(
            '{},{}'.format(m['x'], m['y']) for m in markers),
        'markers': markers,
        'y_max_label': round(global_max, 1),
        'y_min_label': round(global_min, 1),
    }


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
            question.convergence_chart = _convergence_chart(
                question.previous_rounds)

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
