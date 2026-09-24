from django.db import models
from django.utils.translation import gettext_lazy as _

from adhocracy4.projects import models as project_models

from . import engine

FLAG_CHOICES = tuple((flag, flag) for flag in engine.FLAGS)
ACTION_CHOICES = (
    (engine.SET, _('Set')),
    (engine.CLEARED, _('Cleared')),
)


class LogEntry(models.Model):
    """One moderation-flag change on one comment, deliberately without
    a reference to *which* comment, its text, or who moderated it --
    this is a public, aggregate "how much moderation activity is
    happening" changelog, not a detailed per-item audit trail (that
    already exists for admins via Django admin on the Comment/Report
    models directly). Keeping it this anonymized is what makes it safe
    to show to participants at all.
    """

    project = models.ForeignKey(
        project_models.Project,
        on_delete=models.CASCADE,
        related_name='moderation_log_entries',
    )
    flag = models.CharField(max_length=32, choices=FLAG_CHOICES)
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return '{} {} on project {}'.format(
            self.flag, self.action, self.project_id)
