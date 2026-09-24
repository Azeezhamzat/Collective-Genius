from django.template.response import TemplateResponse
from django.views import generic

from adhocracy4.projects.mixins import ProjectMixin

from . import services


class SimilarItemsView(ProjectMixin, generic.View):
    """Standalone check: type in a rough title/description and see
    existing items in this module that already look similar, before
    submitting a new one. No JS -- the query is a plain GET param, so
    this also works as a shareable/bookmarkable link.

    Subclasses set ``item_label`` (used in the template) and override
    ``find_similar`` to call the right services function for their
    model (Idea, Proposal, ...).
    """

    template_name = 'a4_candy_deduplication/similar_items.html'
    item_label = 'idea'

    def find_similar(self, query):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()
        results = []
        if query:
            results = self.find_similar(query)

        context = self.get_context_data()
        context['query'] = query
        context['results'] = results
        context['item_label'] = self.item_label
        return TemplateResponse(request, self.template_name, context)


class SimilarIdeasView(SimilarItemsView):
    item_label = 'idea'

    def find_similar(self, query):
        return services.find_similar_ideas(self.module, query)


class SimilarProposalsView(SimilarItemsView):
    item_label = 'proposal'

    def find_similar(self, query):
        return services.find_similar_proposals(self.module, query)
