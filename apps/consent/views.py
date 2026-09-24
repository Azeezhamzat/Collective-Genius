from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from adhocracy4.projects.mixins import DisplayProjectOrModuleMixin
from adhocracy4.projects.mixins import ProjectMixin

from . import services
from .models import Proposal
from .models import Response


class ProposalListDetail(ProjectMixin, DisplayProjectOrModuleMixin,
                         generic.View):
    """The module's main page for a consent-decision phase: every
    proposal, each with its current consent status and a form to
    respond (agree / stand aside / object), plus a form to add a new
    proposal.

    Registered as a phase view (see phases.py) -- reached through the
    module's own canonical URL, same pattern as apps/quadraticvoting
    and apps/forecasting.
    """

    template_name = 'a4_candy_consent/proposal_list.html'

    def get(self, request, *args, **kwargs):
        return self.render()

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse('account_login')
            return redirect('{}?next={}'.format(login_url, request.path))

        action = request.POST.get('action')
        if action == 'create_proposal':
            return self._create_proposal(request)
        elif action == 'respond':
            return self._respond(request)
        elif action == 'resolve':
            return self._resolve(request)
        return self.render()

    def _create_proposal(self, request):
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        if not title or not description:
            messages.error(request, _(
                'Please fill in both a title and a description.'))
            return self.render()

        Proposal.objects.create(
            module=self.module, creator=request.user,
            title=title, description=description,
        )
        messages.success(request, _('Your proposal was added.'))
        return self.render()

    def _respond(self, request):
        proposal = Proposal.objects.filter(
            module=self.module, pk=request.POST.get('proposal_id')).first()
        if proposal is None:
            return self.render()

        stance = request.POST.get('stance')
        if stance not in (Response.AGREE, Response.STAND_ASIDE,
                          Response.OBJECT):
            messages.error(request, _('Please choose a valid response.'))
            return self.render()

        reason = request.POST.get('reason', '').strip()
        if stance == Response.OBJECT and not reason:
            messages.error(request, _(
                'An objection needs a reason -- what would need to '
                'change for you to withdraw it?'))
            return self.render()

        Response.objects.update_or_create(
            proposal=proposal, creator=request.user,
            defaults={'stance': stance, 'reason': reason,
                     'resolved': False},
        )
        messages.success(request, _('Your response was saved.'))
        return self.render()

    def _resolve(self, request):
        response = Response.objects.filter(
            pk=request.POST.get('response_id'),
            proposal__module=self.module,
        ).first()
        if response is None:
            return self.render()

        proposal = response.proposal
        if request.user not in (response.creator, proposal.creator):
            messages.error(request, _(
                'Only the objector or the proposer can mark an '
                'objection resolved.'))
            return self.render()

        response.resolved = True
        response.save(update_fields=['resolved'])
        messages.success(request, _('Objection marked resolved.'))
        return self.render()

    def render(self):
        return TemplateResponse(
            self.request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proposals = list(Proposal.objects.filter(module=self.module)
                         .select_related('creator'))

        my_responses = {}
        if self.request.user.is_authenticated:
            my_responses = {
                r.proposal_id: r
                for r in Response.objects.filter(
                    proposal__in=proposals, creator=self.request.user)
            }

        for proposal in proposals:
            proposal.result = services.consent_for_proposal(proposal)
            proposal.my_response = my_responses.get(proposal.pk)
            proposal.all_responses = list(
                proposal.responses.select_related('creator'))

        context['proposals'] = proposals
        return context
