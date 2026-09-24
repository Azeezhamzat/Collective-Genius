"""Bridges a module's real ideas to the pure-Python similarity engine.

Unlike apps/synthesis and apps/summarization, ``Idea.module`` is a real,
indexed foreign key (inherited from adhocracy4's ``Item``), so this is a
plain, efficient queryset filter -- no generic-FK walk needed.
"""

from django.utils.html import strip_tags

from apps.ideas.models import Idea

from . import engine


def ideas_for_module(module):
    return Idea.objects.filter(module=module)


def _idea_text(idea):
    return '{} {}'.format(idea.name, strip_tags(idea.description))


def find_similar_ideas(module, query_text, top_n=5, min_score=0.15,
                       exclude_pk=None):
    """Return [(SimilarDocument, Idea), ...] for ideas in ``module`` whose
    text resembles ``query_text``, most similar first.

    ``exclude_pk``: skip this idea (e.g. the one currently being edited,
    so it doesn't show up as "similar to itself").
    """
    ideas = list(ideas_for_module(module))
    if exclude_pk is not None:
        ideas = [i for i in ideas if i.pk != exclude_pk]

    documents = [(str(idea.pk), _idea_text(idea)) for idea in ideas]
    results = engine.find_similar(
        query_text, documents, top_n=top_n, min_score=min_score)

    ideas_by_id = {str(idea.pk): idea for idea in ideas}
    return [
        (result, ideas_by_id[result.doc_id])
        for result in results
        if result.doc_id in ideas_by_id
    ]
