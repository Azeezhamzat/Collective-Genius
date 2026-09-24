"""Flags likely-spam comments for moderator review as they're created,
using the existing ``is_moderator_marked`` field on adhocracy4's
Comment model rather than a new one -- moderators already have a
workflow built around that flag, this just gives it another source.

Advisory only: a flagged comment is still posted and visible, just
marked for a moderator to look at. Nothing here deletes, hides, or
blocks a submission -- a heuristic is never confident enough to justify
silently censoring a real participant, only to ask a human to take a
second look.
"""

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver

from adhocracy4.comments.models import Comment

from . import engine


@receiver(pre_save, sender=Comment)
def flag_likely_spam(sender, instance, **kwargs):
    if instance.pk:
        # Only score brand-new comments -- never re-flag (or silently
        # un-flag) on a later edit, removal, or moderator action that
        # re-saves the same row.
        return

    if not getattr(settings, 'A4_SPAM_DETECTION_ENABLED', True):
        return

    threshold = getattr(settings, 'A4_SPAM_SCORE_THRESHOLD', 0.5)
    if engine.is_likely_spam(instance.comment, threshold=threshold):
        instance.is_moderator_marked = True
