"""Cross-project semantic search: once an organisation has run many
projects, "has anyone already proposed something like this" shouldn't
require remembering which project it was in or matching the exact
words used.

Deliberately reuses ``apps.deduplication.engine`` (TF-IDF + cosine
similarity) rather than duplicating it -- that module was already
written to be a generic "find text similar to this query" engine, not
specific to checking one module for duplicates; this is the same
algorithm applied across every module in every project an organisation
runs, instead of one module at a time. No new engine, no new tests
needed here: the similarity math is already covered by
apps/deduplication/tests/test_engine.py.
"""

from django.utils.html import strip_tags

from apps.deduplication import engine as similarity_engine


def _searchable_models():
    # Imported lazily to avoid a hard import-time dependency between
    # apps -- these are only needed once a search actually runs.
    from apps.budgeting.models import Proposal
    from apps.debate.models import Subject
    from apps.ideas.models import Idea
    from apps.mapideas.models import MapIdea
    return [Idea, Proposal, MapIdea, Subject]


def items_for_organisation(organisation):
    for model in _searchable_models():
        for item in model.objects.filter(
                module__project__organisation=organisation):
            yield item


def _item_text(item):
    description = getattr(item, 'description', '') or ''
    return '{} {}'.format(item.name, strip_tags(description))


def search_organisation(organisation, query_text, top_n=10, min_score=0.15):
    """Return [(SimilarDocument, item), ...] across every Idea,
    Proposal, MapIdea and debate Subject in every project belonging to
    ``organisation``, most similar to ``query_text`` first.

    Uses a positional index as the document id rather than each item's
    own pk: pks aren't unique *across* different models (an Idea #1 and
    a Proposal #1 can both exist), so reusing them here would silently
    collide.
    """
    items = list(items_for_organisation(organisation))
    documents = [
        (str(index), _item_text(item)) for index, item in enumerate(items)
    ]
    results = similarity_engine.find_similar(
        query_text, documents, top_n=top_n, min_score=min_score)

    items_by_id = {str(index): item for index, item in enumerate(items)}
    return [
        (result, items_by_id[result.doc_id])
        for result in results
        if result.doc_id in items_by_id
    ]
