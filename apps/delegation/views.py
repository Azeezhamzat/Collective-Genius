from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from adhocracy4.dashboard import mixins as dashboard_mixins
from adhocracy4.projects.mixins import DisplayProjectOrModuleMixin
from adhocracy4.projects.mixins import ProjectMixin

from . import services
from .models import DelegationRound
from .models import Option

OptionFormSet = forms.inlineformset_factory(
    DelegationRound, Option,
    fields=('title', 'description', 'weight'),
    extra=3, can_delete=True,
)

DelegationRoundForm = forms.modelform_factory(
    DelegationRound,
    fields=('title', 'description', 'is_open'),
)


class DelegationRoundDetail(ProjectMixin, DisplayProjectOrModuleMixin,
                            generic.View):
    """The module's main page for a liquid-democracy round: cast a
    direct vote, delegate to another participant, or revoke either.

    Registered as a phase view (see phases.py), so this is reached
    through the module's own canonical URL, same as
    apps/quadraticvoting -- no separate urls.py for this app.
    """

    template_name = 'a4_candy_delegation/delegationround_detail.html'

    def get(self, request, *args, **kwargs):
        return self.render()

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse('account_login')
            return redirect('{}?next={}'.format(login_url, request.path))

        delegation_round = self.get_round()
        if delegation_round is None or not delegation_round.is_open:
            messages.error(request, _('This round is not open.'))
            return self.render()

        action = request.POST.get('action')
        if action == 'revoke':
            services.revoke(delegation_round, request.user)
            messages.success(request, _('Your choice was cleared.'))
            return self.render()

        if action == 'delegate':
            delegatee_username = request.POST.get('delegatee')
            delegatee = self._resolve_delegatee(delegatee_username)
            if delegatee is None:
                messages.error(request, _(
                    'Please choose a valid person to delegate to.'))
                return self.render()
            if delegatee.pk == request.user.pk:
                messages.error(
                    request, _('You cannot delegate to yourself.'))
                return self.render()
            services.cast_delegation(delegation_round, request.user,
                                     delegatee)
            messages.success(request, _(
                'Your vote is now delegated to %(name)s.'
            ) % {'name': str(delegatee)})
            return self.render()

        option_id = request.POST.get('option')
        option = delegation_round.options.filter(pk=option_id).first()
        if option is None:
            messages.error(request, _('Please choose a valid option.'))
            return self.render()
        services.cast_vote(delegation_round, request.user, option)
        messages.success(request, _('Your vote was saved.'))
        return self.render()

    def _resolve_delegatee(self, username):
        if not username:
            return None
        try:
            return get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist:
            return None

    def get_round(self):
        return DelegationRound.objects.filter(module=self.module).first()

    def render(self):
        return TemplateResponse(
            self.request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        delegation_round = self.get_round()
        context['delegation_round'] = delegation_round
        if delegation_round is None:
            return context

        if self.request.user.is_authenticated:
            action, target = services.my_choice(
                delegation_round, self.request.user)
            context['my_action'] = action
            context['my_target'] = target

        if not delegation_round.is_open:
            results = services.tally_round(delegation_round)
            context['results_by_option_id'] = {
                int(r.option_id): r.votes for r in results
            }
            context['voting_power'] = services.voting_power_for_round(
                delegation_round)

        return context


class DelegationRoundDashboardView(ProjectMixin,
                                   dashboard_mixins.DashboardBaseMixin,
                                   dashboard_mixins.DashboardComponentMixin,
                                   generic.View):
    """Lets a project admin manage a module's delegation round and its
    options without touching /django-admin/. Hand-written rather than
    built on ``ModuleFormSetComponent`` for the same reason as
    apps/quadraticvoting's dashboard view: Options hang off a
    DelegationRound, one level below the Module.
    """

    template_name = 'a4_candy_delegation/delegationround_dashboard.html'
    permission_required = 'a4projects.change_project'
    component = None  # set via as_view(component=self) in dashboard.py

    def get_permission_object(self):
        return self.project

    def get_or_create_round(self):
        delegation_round, _created = DelegationRound.objects.get_or_create(
            module=self.module,
            defaults={'title': self.module.name},
        )
        return delegation_round

    def get(self, request, *args, **kwargs):
        delegation_round = self.get_or_create_round()
        round_form = DelegationRoundForm(instance=delegation_round)
        formset = OptionFormSet(instance=delegation_round)
        return self.render(round_form, formset)

    def post(self, request, *args, **kwargs):
        delegation_round = self.get_or_create_round()
        round_form = DelegationRoundForm(
            request.POST, instance=delegation_round)
        formset = OptionFormSet(request.POST, instance=delegation_round)

        if round_form.is_valid() and formset.is_valid():
            round_form.save()
            formset.save()
            messages.success(request, _('Delegation round saved.'))
            return redirect(request.path)

        return self.render(round_form, formset)

    def render(self, round_form, formset):
        context = self.get_context_data()
        context['round_form'] = round_form
        context['formset'] = formset
        return TemplateResponse(self.request, self.template_name, context)
