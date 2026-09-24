from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from adhocracy4.dashboard import DashboardComponent
from adhocracy4.dashboard import components

from . import views


class FacilitatorToolkitComponent(DashboardComponent):
    identifier = 'facilitator'
    weight = 90
    label = _('Facilitator toolkit')

    def is_effective(self, project):
        return True

    def get_base_url(self, project):
        return reverse('a4dashboard:facilitator-toolkit', kwargs={
            'organisation_slug': project.organisation.slug,
            'project_slug': project.slug,
        })

    def get_urls(self):
        return [(
            r'^projects/(?P<project_slug>[-\w_]+)/facilitator/$',
            views.FacilitatorToolkitView.as_view(component=self),
            'facilitator-toolkit',
        )]


components.register_project(FacilitatorToolkitComponent())
