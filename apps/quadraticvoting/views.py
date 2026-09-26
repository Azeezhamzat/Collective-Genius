from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from adhocracy4.dashboard import mixins as dashboard_mixins
from adhocracy4.projects.mixins import DisplayProjectOrModuleMixin
from adhocracy4.projects.mixins import ProjectMixin

from . import services
from .models import Option
from .models import VotingRound
from .services import BallotRejected

OptionFormSet = forms.inlineformset_factory(
    VotingRound, Option,
    fields=('title', 'description', 'weight'),
    extra=3, can_delete=True,
)

VotingRoundForm = forms.modelform_factory(
    VotingRound,
    fields=('title', 'description', 'credit_budget', 'is_open'),
)


class VotingRoundDetail(ProjectMixin, DisplayProjectOrModuleMixin,
                        generic.View):
    """The module's main page for a quadratic-voting phase.

    Registered as a phase view (see phases.py), so this is reached
    through the module's own canonical URL while the voting phase is
    active/last-active -- there is no separate urls.py for this app, same
    as apps/polls.
    """

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
            context['max_side_votes'] = max(
                [max(r.support_votes, r.oppose_votes) for r in results]
                or [0])
            context['total_voters'] = len(
                {a.creator_id for a in
                 services.allocations_for_round(voting_round)})

        return context


class VotingRoundDashboardView(ProjectMixin,
                               dashboard_mixins.DashboardBaseMixin,
                               dashboard_mixins.DashboardComponentMixin,
                               generic.View):
    """Lets a project admin manage a module's voting round and its
    options without touching /django-admin/.

    Deliberately hand-written rather than built on
    ``adhocracy4.dashboard.ModuleFormSetComponent``: that base class
    assumes the formset's parent instance is the Module itself, but our
    Options hang off a VotingRound, one level below the Module -- so a
    plain get-or-create-then-render-two-forms view is more correct here
    than forcing a mismatched abstraction.
    """

    template_name = 'a4_candy_quadraticvoting/votinground_dashboard.html'
    permission_required = 'a4projects.change_project'
    component = None  # set via as_view(component=self) in dashboard.py

    def get_permission_object(self):
        return self.project

    def get_or_create_voting_round(self):
        voting_round, _created = VotingRound.objects.get_or_create(
            module=self.module,
            defaults={'title': self.module.name},
        )
        return voting_round

    def get(self, request, *args, **kwargs):
        voting_round = self.get_or_create_voting_round()
        round_form = VotingRoundForm(instance=voting_round)
        formset = OptionFormSet(instance=voting_round)
        return self.render(round_form, formset)

    def post(self, request, *args, **kwargs):
        voting_round = self.get_or_create_voting_round()
        round_form = VotingRoundForm(request.POST, instance=voting_round)
        formset = OptionFormSet(request.POST, instance=voting_round)

        if round_form.is_valid() and formset.is_valid():
            round_form.save()
            formset.save()
            messages.success(request, _('Voting round saved.'))
            return redirect(request.path)

        return self.render(round_form, formset)

    def render(self, round_form, formset):
        context = self.get_context_data()
        context['round_form'] = round_form
        context['formset'] = formset
        return TemplateResponse(self.request, self.template_name, context)
