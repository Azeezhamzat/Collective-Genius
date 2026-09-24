from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views import generic

from adhocracy4.projects.models import Project

from . import services


class OpenDataMixin:

    def get_project(self):
        project = get_object_or_404(
            Project, slug=self.kwargs['project_slug'])
        if not project.is_public:
            # Never serve a private or semi-public project's content
            # through this unauthenticated export -- 404 rather than
            # 403 so the export doesn't itself reveal that a
            # non-public project exists at this slug.
            raise Http404
        return project


class OpenDataIndexView(OpenDataMixin, generic.View):
    """A small public landing page explaining what the export contains
    and linking to the actual JSON download, rather than dropping a
    visitor straight into a raw JSON file with no context.
    """

    template_name = 'a4_candy_opendata/index.html'

    def get(self, request, *args, **kwargs):
        project = self.get_project()
        return TemplateResponse(
            request, self.template_name, {'project': project})


class OpenDataExportView(OpenDataMixin, generic.View):

    def get(self, request, *args, **kwargs):
        project = self.get_project()
        generated_at = timezone.now().isoformat()
        dataset = services.build_export(project, generated_at)
        response = JsonResponse(dataset)
        filename = '{}-{}.json'.format(
            project.slug, timezone.now().strftime('%Y-%m-%d'))
        response['Content-Disposition'] = \
            'attachment; filename="{}"'.format(filename)
        return response
