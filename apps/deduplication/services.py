"""Bridges a module's real items (ideas, budgeting proposals, ...) to
the pure-Python similarity engine.

Unlike apps/synthesis and apps/summarization, these models have a real,
indexed ``module`` foreign key (inherited from adhocracy4's ``Item``),
so this is a plain, efficient queryset filter -- no generic-FK walk
needed.
"""

from django.utils.html import strip_tags

from . import engine


def items_for_module(model, module):
    return model.objects.filter(module=module)


def _item_text(item):
    return '{} {}'.format(item.name, strip_tags(item.description))


def find_similar_items(model, module, query_text, top_n=5, min_score=0.15,
                       exclude_pk=None):
    """Return [(SimilarDocument, item), ...] for ``model`` instances in
    ``module`` whose text resembles ``query_text``, most similar first.

    ``model`` must have ``.module``, ``.name`` and ``.description``
    fields -- true of Idea, Proposal (budgeting), and any other
    adhocracy4 Item subclass built the same way.

    ``exclude_pk``: skip this item (e.g. the one currently being
    edited, so it doesn't show up as "similar to itself").
    """
    items = list(items_for_module(model, module))
    if exclude_pk is not None:
        items = [i for i in items if i.pk != exclude_pk]

    documents = [(str(item.pk), _item_text(item)) for item in items]
    results = engine.find_similar(
        query_text, documents, top_n=top_n, min_score=min_score)

    items_by_id = {str(item.pk): item for item in items}
    return [
        (result, items_by_id[result.doc_id])
        for result in results
        if result.doc_id in items_by_id
    ]


def find_similar_ideas(module, query_text, **kwargs):
    from apps.ideas.models import Idea
    return find_similar_items(Idea, module, query_text, **kwargs)


def find_similar_proposals(module, query_text, **kwargs):
    from apps.budgeting.models import Proposal
    return find_similar_items(Proposal, module, query_text, **kwargs)
