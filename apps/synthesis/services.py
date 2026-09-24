"""Bridges Collective Genius' real data (adhocracy4 Comments + Ratings) to
the pure-Python synthesis engine in ``engine.py``, and persists the result.

``Comment.module`` and ``Rating.module``/``Rating.project`` are *computed*
properties in the adhocracy4 version this project pins -- there is no
indexed ``module`` column on either model -- so finding "every comment in
this module" means walking every comment and checking the property in
Python. That's fine for the scale a single module's discussion reaches; if
it ever becomes a bottleneck, the right fix is an indexed ``module`` field
on ``Comment`` upstream in adhocracy4, not a workaround here.
"""

from django.contrib.contenttypes.models import ContentType

from adhocracy4.comments.models import Comment
from adhocracy4.ratings.models import Rating

from . import engine
from .models import StatementResult
from .models import SynthesisSnapshot


def comments_for_module(module):
    """Every (non-removed, non-censored) comment that belongs to
    ``module``."""
    for comment in Comment.objects.filter(is_removed=False,
                                          is_censored=False):
        try:
            comment_module = comment.module
        except AttributeError:
            # content_object was deleted or doesn't resolve a module;
            # skip rather than fail the whole run.
            continue
        if comment_module and comment_module.pk == module.pk:
            yield comment


def votes_for_module(module):
    """Build the list of engine.Vote for every rating on every comment in
    ``module``.

    A comment's ``+1``/``-1`` rating is treated as an "agree"/"disagree"
    vote on that comment as a statement -- the same semantics Polis-style
    tools use for a statement's votes.
    """
    comment_ct = ContentType.objects.get_for_model(Comment)
    result = []
    for comment in comments_for_module(module):
        ratings = Rating.objects.filter(
            content_type=comment_ct, object_pk=comment.pk
        ).exclude(value=0)
        for rating in ratings:
            result.append(engine.Vote(
                participant_id=str(rating.creator_id),
                statement_id=str(comment.pk),
                value=engine.AGREE if rating.value == Rating.POSITIVE
                else engine.DISAGREE,
            ))
    return result


def run_synthesis(module, min_votes_per_statement=3):
    """Run the synthesis engine for ``module`` and persist a new snapshot.

    Returns the created ``SynthesisSnapshot``. Statements without enough
    votes to say anything meaningful are left out of the stored results,
    but still count towards ``n_statements`` on the snapshot for context.
    """
    votes = votes_for_module(module)
    result = engine.analyze(
        votes, min_votes_per_statement=min_votes_per_statement)

    snapshot = SynthesisSnapshot.objects.create(
        module=module,
        n_participants=len(result.groups),
        n_statements=len({v.statement_id for v in votes}),
        n_groups=result.n_groups,
        group_sizes={str(k): v for k, v in result.group_sizes.items()},
    )

    comments_by_id = {
        str(c.pk): c for c in Comment.objects.filter(
            pk__in=[s.statement_id for s in result.statements])
    }

    StatementResult.objects.bulk_create([
        StatementResult(
            snapshot=snapshot,
            comment=comments_by_id[s.statement_id],
            n_votes=s.n_votes,
            agree_ratio=s.agree_ratio,
            consensus_score=s.consensus_score,
            divisiveness=s.divisiveness,
        )
        for s in result.statements
        if s.statement_id in comments_by_id
    ])

    return snapshot
