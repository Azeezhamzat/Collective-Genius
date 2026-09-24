"""Bridges the real comment tree (adhocracy4 Comment + our own Stance) to
the pure-Python engine in ``engine.py``.
"""

from adhocracy4.comments.models import Comment

from . import engine
from .models import Stance


def root_content_object(comment):
    """Walk a comment's content_object chain past any nested replies to
    the actual thing being discussed (e.g. a debate Subject).

    A reply's content_object is the comment it replies to; that comment's
    content_object is in turn either another comment or the real subject
    -- walk until it isn't a Comment any more.
    """
    obj = comment.content_object
    while isinstance(obj, Comment):
        obj = obj.content_object
    return obj


def comments_for_subject(subject):
    """Every (non-removed, non-censored) comment anywhere in the
    discussion tree under ``subject``, at any depth.

    Same caveat as apps/synthesis/services.py: Comment has no indexed FK
    back to what it's ultimately about, only a chain of generic foreign
    keys, so this walks every comment in the database and checks in
    Python. Fine at the scale a single debate reaches; an indexed
    ``module``/root field on Comment upstream in adhocracy4 would be the
    real fix if this becomes a bottleneck.
    """
    for comment in Comment.objects.filter(is_removed=False,
                                          is_censored=False):
        try:
            root = root_content_object(comment)
        except AttributeError:
            continue
        if root == subject:
            yield comment


def build_argument_map(subject):
    """Return (trees, comments_by_id) for ``subject``: the scored,
    sorted forest from engine.build_argument_map, and a lookup from
    stringified comment pk to the actual Comment instance, for the view
    to render text/author from.
    """
    comments = list(comments_for_subject(subject))
    stances = {
        s.comment_id: s.value
        for s in Stance.objects.filter(comment__in=comments)
    }

    raw_nodes = []
    for comment in comments:
        parent = comment.content_object
        parent_id = str(parent.pk) if isinstance(parent, Comment) else None
        raw_nodes.append(engine.RawNode(
            id=str(comment.pk),
            parent_id=parent_id,
            stance=stances.get(comment.pk),
        ))

    trees = engine.build_argument_map(raw_nodes)
    comments_by_id = {str(c.pk): c for c in comments}
    return trees, comments_by_id
