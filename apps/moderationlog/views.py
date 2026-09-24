from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views import generic

from adhocracy4.projects.models import Project

from . import services


class ModerationLogView(generic.View):
    """A public, aggregate changelog of moderation activity on a
    project -- deliberately anonymized (no comment content, no
    moderator identity, see the LogEntry model docstring) so it's safe
    to show to any participant as evidence that moderation is
    happening, without exposing what was said or by whom.
    """

    template_name = 'a4_candy_moderationlog/log.html'

    def get_project(self):
        return get_object_or_404(
            Project, slug=self.kwargs['project_slug'])

    def get(self, request, *args, **kwargs):
        project = self.get_project()
        context = {
            'project': project,
            'entries': services.entries_for_project(project),
            'summary': services.summary_for_project(project),
        }
        return TemplateResponse(request, self.template_name, context)
