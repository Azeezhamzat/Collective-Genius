from django.template.response import TemplateResponse
from django.views import generic

from adhocracy4.projects.mixins import ProjectMixin

from . import services


class SimilarIdeasView(ProjectMixin, generic.View):
    """Standalone check: type in a rough title/description and see
    existing ideas in this module that already look similar, before
    submitting a new one. No JS -- the query is a plain GET param, so
    this also works as a shareable/bookmarkable link.
    """

    template_name = 'a4_candy_deduplication/similar_ideas.html'

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()
        results = []
        if query:
            results = services.find_similar_ideas(self.module, query)

        context = self.get_context_data()
        context['query'] = query
        context['results'] = results
        return TemplateResponse(request, self.template_name, context)
