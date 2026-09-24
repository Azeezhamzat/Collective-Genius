"""Bridges a project's real comments/reports to the facilitator toolkit.

Same "no indexed FK for this, so it's a full table scan" caveat as
apps/synthesis and apps/summarization: ``Comment.project`` is a computed
property, not an indexed column, in the adhocracy4 version this project
pins.
"""

from django.contrib.contenttypes.models import ContentType

from adhocracy4.comments.models import Comment
from adhocracy4.reports.models import Report

from . import engine


def comments_for_project(project):
    """Every (non-removed, non-censored) comment anywhere in ``project``,
    across all of its modules."""
    for comment in Comment.objects.filter(is_removed=False,
                                          is_censored=False):
        try:
            comment_project = comment.project
        except AttributeError:
            continue
        if comment_project and comment_project.pk == project.pk:
            yield comment


def reported_comments_for_project(project):
    """Comments in ``project`` that have at least one open report,
    most-reported first. Each entry is (comment, report_count)."""
    comment_ct = ContentType.objects.get_for_model(Comment)
    comments = list(comments_for_project(project))
    comment_ids = {c.pk for c in comments}
    if not comment_ids:
        return []

    reports = Report.objects.filter(
        content_type=comment_ct, object_pk__in=comment_ids)
    counts = {}
    for report in reports:
        counts[report.object_pk] = counts.get(report.object_pk, 0) + 1

    comments_by_id = {c.pk: c for c in comments}
    results = [
        (comments_by_id[object_pk], count)
        for object_pk, count in counts.items()
        if object_pk in comments_by_id
    ]
    results.sort(key=lambda pair: pair[1], reverse=True)
    return results


def activity_summary(project, days=7):
    """engine.DayCount list for comment activity in ``project`` over the
    last ``days`` days."""
    timestamps = [c.created for c in comments_for_project(project)]
    return engine.bucket_by_day(timestamps, days=days)
