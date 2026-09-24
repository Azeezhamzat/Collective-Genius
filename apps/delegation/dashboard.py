from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from adhocracy4.dashboard import DashboardComponent
from adhocracy4.dashboard import components

from . import apps
from . import views
from .models import Option


class DelegationRoundComponent(DashboardComponent):
    identifier = 'delegation'
    weight = 20
    label = _('Options')

    def is_effective(self, module):
        module_app = module.phases[0].content().app
        return module_app == apps.Config.label

    def get_progress(self, module):
        if Option.objects.filter(delegation_round__module=module).exists():
            return 1, 1
        return 0, 1

    def get_base_url(self, module):
        return reverse('a4dashboard:delegation-edit', kwargs={
            'organisation_slug': module.project.organisation.slug,
            'module_slug': module.slug,
        })

    def get_urls(self):
        return [(
            r'^modules/(?P<module_slug>[-\w_]+)/delegation/$',
            views.DelegationRoundDashboardView.as_view(component=self),
            'delegation-edit',
        )]


components.register_module(DelegationRoundComponent())
