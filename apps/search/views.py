from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views import generic

from apps.organisations.models import Organisation

from . import services


class OrganisationSearchView(generic.View):
    """Organisation-wide "search by meaning" across every idea,
    proposal, map-idea and debate subject in every project the
    organisation runs. No JS -- the query is a plain GET param, so
    this also works as a shareable/bookmarkable link.
    """

    template_name = 'a4_candy_search/search.html'

    def get_organisation(self):
        return get_object_or_404(
            Organisation, slug=self.kwargs['organisation_slug'])

    def get(self, request, *args, **kwargs):
        organisation = self.get_organisation()
        query = request.GET.get('q', '').strip()
        results = []
        if query:
            results = services.search_organisation(organisation, query)

        context = {
            'organisation': organisation,
            'query': query,
            'results': results,
        }
        return TemplateResponse(request, self.template_name, context)
