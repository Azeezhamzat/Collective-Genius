from django.db import models

from adhocracy4.comments import models as comment_models
from adhocracy4.modules import models as module_models


class SynthesisSnapshot(models.Model):
    """One run of the synthesis engine over a module's comments."""

    module = models.ForeignKey(
        module_models.Module,
        on_delete=models.CASCADE,
        related_name='synthesis_snapshots',
    )
    created = models.DateTimeField(auto_now_add=True)
    n_participants = models.PositiveIntegerField(default=0)
    n_statements = models.PositiveIntegerField(default=0)
    n_groups = models.PositiveIntegerField(default=0)
    group_sizes = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ('-created',)
        get_latest_by = 'created'

    def __str__(self):
        return 'Synthesis of {} at {}'.format(self.module, self.created)


class StatementResult(models.Model):
    """Consensus/divisiveness score for a single comment within a
    snapshot."""

    snapshot = models.ForeignKey(
        SynthesisSnapshot,
        on_delete=models.CASCADE,
        related_name='statement_results',
    )
    comment = models.ForeignKey(
        comment_models.Comment,
        on_delete=models.CASCADE,
        related_name='synthesis_results',
    )
    n_votes = models.PositiveIntegerField()
    agree_ratio = models.FloatField()
    consensus_score = models.FloatField()
    divisiveness = models.FloatField()

    class Meta:
        ordering = ('-consensus_score',)

    def __str__(self):
        return 'StatementResult(comment={}, consensus={:.2f})'.format(
            self.comment_id, self.consensus_score)

    @property
    def is_bridging(self):
        """High agreement in every opinion group -- genuine consensus."""
        return self.consensus_score >= 0.6 and self.n_votes >= 3

    @property
    def is_divisive(self):
        """Opinion groups pull in opposite directions on this statement."""
        return self.divisiveness >= 0.6 and self.n_votes >= 3
