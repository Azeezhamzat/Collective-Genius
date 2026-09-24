from django.db.models import Count

from .models import LogEntry


def entries_for_project(project, limit=100):
    return LogEntry.objects.filter(project=project)[:limit]


def summary_for_project(project):
    """{(flag, action): count} across every logged entry for
    ``project`` -- a quick "how much of each kind of moderation
    activity has happened here" summary."""
    rows = (
        LogEntry.objects.filter(project=project)
        .values('flag', 'action')
        .annotate(count=Count('id'))
    )
    return {(row['flag'], row['action']): row['count'] for row in rows}
