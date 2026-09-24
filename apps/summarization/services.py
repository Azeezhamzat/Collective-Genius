"""Bridges a module's real comments to the pure-Python summarization
engine, and persists the result.

Same technique (and the same "no indexed FK for this, so it's a full
table scan" caveat) as apps/synthesis/services.py: ``Comment.module`` is
a computed property in the adhocracy4 version this project pins, not an
indexed database column.
"""

from adhocracy4.comments.models import Comment

from . import backends
from . import engine
from .models import KeyComment
from .models import SummarySnapshot


def comments_for_module(module):
    """Every (non-removed, non-censored) comment that belongs to
    ``module``."""
    for comment in Comment.objects.filter(is_removed=False,
                                          is_censored=False):
        try:
            comment_module = comment.module
        except AttributeError:
            continue
        if comment_module and comment_module.pk == module.pk:
            yield comment


def run_summarization(module, top_n=5, min_significant_words=3):
    """Summarize ``module``'s comments and persist a new snapshot.

    Returns the created SummarySnapshot.
    """
    comments = list(comments_for_module(module))
    pairs = [(str(c.pk), c.comment) for c in comments]

    scored = backends.summarize(
        pairs, top_n=top_n, min_significant_words=min_significant_words)
    # Keyword extraction stays extractive-only: it's a plain word-frequency
    # statistic, not worth an LLM call.
    keywords = engine.top_keywords(pairs, top_n=10)

    snapshot = SummarySnapshot.objects.create(
        module=module,
        n_comments=len(comments),
        keywords=[word for word, _count in keywords],
    )

    comments_by_id = {str(c.pk): c for c in comments}
    KeyComment.objects.bulk_create([
        KeyComment(
            snapshot=snapshot,
            comment=comments_by_id[s.comment_id],
            score=s.score,
            rank=rank,
        )
        for rank, s in enumerate(scored, start=1)
        if s.comment_id in comments_by_id
    ])

    return snapshot
