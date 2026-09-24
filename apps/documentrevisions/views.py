from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views import generic

from apps.documents.models import Paragraph

from . import services


class ParagraphHistoryView(generic.View):
    """Read-only revision history for one paragraph. Linked from the
    chapter page next to the comments link.
    """

    template_name = 'a4_candy_documentrevisions/paragraph_history.html'

    def get(self, request, *args, **kwargs):
        paragraph = get_object_or_404(Paragraph, pk=kwargs['pk'])
        context = {
            'paragraph': paragraph,
            'chapter': paragraph.chapter,
            'revisions': services.history_for_paragraph(paragraph),
        }
        return TemplateResponse(request, self.template_name, context)
