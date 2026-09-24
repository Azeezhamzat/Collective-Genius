"""Assembles the versioned open-data export (apps/opendata/engine.py)
from real project data. Not unit tested here -- it's a thin Django
query layer with no interesting logic of its own; the format/checksum
logic it feeds is what's tested.

Deliberately public-safe by construction:

* Only callable for projects where ``project.is_public`` is true (the
  view enforces this before calling in) -- a private or semi-public
  project's content must never reach this unauthenticated export.
* Item rows include the text a visitor can already read on the item's
  own public page (name/description) -- nothing new is exposed there.
* Comment rows include comment text (also already public on the page
  it's attached to) but never the commenter's identity.
* Rating rows are aggregate counts per item, never individual ratings
  -- who voted which way is not exposed, consistent with
  ``apps/moderationlog``'s anonymization approach.
* Only top-level comments on items are included in this first version,
  not replies-to-comments (which would need recursing through
  arbitrarily deep comment threads); the existing per-module CSV export
  and public comment pages already cover those.
"""

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.utils.html import strip_tags

from . import engine


def _item_models():
    # Imported lazily, same reasoning as apps/search/services.py: avoid
    # a hard import-time dependency between apps that only matters once
    # an export actually runs.
    from apps.budgeting.models import Proposal
    from apps.debate.models import Subject
    from apps.ideas.models import Idea
    from apps.mapideas.models import MapIdea
    return [Idea, Proposal, MapIdea, Subject]


def _items_by_model(project):
    for model in _item_models():
        content_type = ContentType.objects.get_for_model(model)
        for item in model.objects.filter(module__project=project):
            yield content_type, item


def items_section(project):
    rows = []
    for content_type, item in _items_by_model(project):
        rows.append({
            'id': item.pk,
            'type': content_type.model,
            'module': item.module.slug,
            'name': getattr(item, 'name', ''),
            'description': strip_tags(getattr(item, 'description', '') or ''),
            'category': str(getattr(item, 'category', '') or ''),
            'created': item.created.isoformat(),
        })
    return rows


def comments_section(project):
    from adhocracy4.comments.models import Comment

    rows = []
    for content_type, item in _items_by_model(project):
        comments = Comment.objects.filter(
            content_type=content_type, object_pk=item.pk)
        for comment in comments:
            rows.append({
                'id': comment.pk,
                'item_type': content_type.model,
                'item_id': item.pk,
                'text': strip_tags(comment.comment),
                'is_censored': comment.is_censored,
                'is_removed': comment.is_removed,
                'created': comment.created.isoformat(),
            })
    return rows


def ratings_section(project):
    from adhocracy4.ratings.models import Rating

    rows = []
    for content_type, item in _items_by_model(project):
        counts = Rating.objects.filter(
            content_type=content_type, object_pk=item.pk
        ).values('value').annotate(count=Count('id'))
        by_value = {row['value']: row['count'] for row in counts}
        if not by_value:
            continue
        rows.append({
            'item_type': content_type.model,
            'item_id': item.pk,
            'positive': by_value.get(Rating.POSITIVE, 0),
            'negative': by_value.get(Rating.NEGATIVE, 0),
        })
    return rows


def build_export(project, generated_at):
    sections = {
        'items': items_section(project),
        'comments': comments_section(project),
        'ratings': ratings_section(project),
    }
    return engine.build_dataset(project.slug, generated_at, sections)
