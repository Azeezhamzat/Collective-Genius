from django.views import generic

from adhocracy4.dashboard import mixins as dashboard_mixins
from adhocracy4.projects.mixins import ProjectMixin

from . import services


class FacilitatorToolkitView(ProjectMixin,
                             dashboard_mixins.DashboardBaseMixin,
                             dashboard_mixins.DashboardComponentMixin,
                             generic.TemplateView):
    """Project-wide moderator view: recent activity, comments that have
    been reported, and quick links into each module's Synthesis/
    Summarization pages. Reachable from the project dashboard, so it's
    gated by the same 'a4projects.change_project' permission as every
    other dashboard page -- nothing here is public.
    """

    template_name = 'a4_candy_facilitator/toolkit.html'
    permission_required = 'a4projects.change_project'
    component = None  # set via as_view(component=self) in dashboard.py

    def get_permission_object(self):
        return self.project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity'] = services.activity_summary(self.project)
        context['activity_total'] = sum(
            day.count for day in context['activity'])
        context['reported_comments'] = \
            services.reported_comments_for_project(self.project)
        context['modules'] = self.project.module_set.filter(
            is_draft=False)
        return context
