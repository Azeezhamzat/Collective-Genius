def log_comment_moderation_changes(sender, instance, **kwargs):
    """Before a Comment is saved, compare its moderation flags
    (is_censored/is_removed/is_blocked) against what's currently in the
    database and record a LogEntry for anything that changed -- a
    moderator censoring, removing, blocking, or reversing any of those
    on a comment.

    A no-op for a brand new (unsaved) comment: creating a comment isn't
    a moderation action.
    """
    from . import engine
    from .models import LogEntry

    if not instance.pk:
        return

    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    old_flags = {flag: getattr(previous, flag) for flag in engine.FLAGS}
    new_flags = {flag: getattr(instance, flag) for flag in engine.FLAGS}
    changes = engine.diff_moderation_flags(old_flags, new_flags)
    if not changes:
        return

    try:
        project = instance.project
    except AttributeError:
        project = None
    if project is None:
        return

    LogEntry.objects.bulk_create([
        LogEntry(project=project, flag=change.flag, action=change.action)
        for change in changes
    ])
