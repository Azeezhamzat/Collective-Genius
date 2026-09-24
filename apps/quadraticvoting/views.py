from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from adhocracy4.projects.mixins import ProjectMixin

from . import services
from .models import VotingRound
from .services import BallotRejected


class VotingRoundDetail(ProjectMixin, generic.View):
    template_name = 'a4_candy_quadraticvoting/votinground_detail.html'

    def get(self, request, *args, **kwargs):
        return self.render()

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse('account_login')
            return redirect('{}?next={}'.format(login_url, request.path))

        voting_round = self.get_voting_round()
        if voting_round is None or not voting_round.is_open:
            messages.error(request, _('This voting round is not open.'))
            return self.render()

        votes_by_option_id = {}
        for option in voting_round.options.all():
            raw = request.POST.get('votes_{}'.format(option.pk), '0')
            try:
                votes_by_option_id[option.pk] = int(raw)
            except ValueError:
                votes_by_option_id[option.pk] = 0

        try:
            services.save_ballot(
                voting_round, request.user, votes_by_option_id)
        except BallotRejected as err:
            error = err.errors[0]
            messages.error(request, _(
                'Your ballot costs %(spent)d credits, but you only have '
                '%(budget)d. Nothing was saved -- please adjust your '
                'votes and try again.'
            ) % {'spent': error.spent, 'budget': error.budget})
            return self.render()

        messages.success(request, _('Your ballot was saved.'))
        return self.render()

    def get_voting_round(self):
        return VotingRound.objects.filter(module=self.module).first()

    def render(self):
        return TemplateResponse(
            self.request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voting_round = self.get_voting_round()
        context['voting_round'] = voting_round
        if voting_round is None:
            return context

        if self.request.user.is_authenticated:
            context['my_ballot'] = services.ballot_for_participant(
                voting_round, self.request.user)
        else:
            context['my_ballot'] = {}

        if not voting_round.is_open:
            results = services.tally_round(voting_round)
            context['results_by_option_id'] = {
                int(r.option_id): r for r in results
            }

        return context
