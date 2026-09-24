from django.db import models

from adhocracy4.comments import models as comment_models
from adhocracy4.modules import models as module_models


class SummarySnapshot(models.Model):
    """One run of the summarizer over a module's comments."""

    module = models.ForeignKey(
        module_models.Module,
        on_delete=models.CASCADE,
        related_name='summary_snapshots',
    )
    created = models.DateTimeField(auto_now_add=True)
    n_comments = models.PositiveIntegerField(default=0)
    keywords = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ('-created',)
        get_latest_by = 'created'

    def __str__(self):
        return 'Summary of {} at {}'.format(self.module, self.created)


class KeyComment(models.Model):
    """One comment picked out as representative in a snapshot."""

    snapshot = models.ForeignKey(
        SummarySnapshot,
        on_delete=models.CASCADE,
        related_name='key_comments',
    )
    comment = models.ForeignKey(
        comment_models.Comment,
        on_delete=models.CASCADE,
        related_name='summary_appearances',
    )
    score = models.FloatField()
    rank = models.PositiveIntegerField()

    class Meta:
        ordering = ('rank',)

    def __str__(self):
        return 'KeyComment(comment={}, rank={})'.format(
            self.comment_id, self.rank)
