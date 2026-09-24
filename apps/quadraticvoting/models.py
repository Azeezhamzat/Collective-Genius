from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from adhocracy4.modules import models as module_models


class VotingRound(models.Model):
    """A quadratic-voting round: a fixed voice-credit budget that
    participants spread across a set of options."""

    module = models.ForeignKey(
        module_models.Module,
        on_delete=models.CASCADE,
        related_name='quadratic_voting_rounds',
    )
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = models.TextField(blank=True,
                                   verbose_name=_('Description'))
    credit_budget = models.PositiveIntegerField(
        default=100,
        verbose_name=_('Voice credit budget'),
        help_text=_(
            'How many credits each participant can spend in total across '
            'all options. Casting N votes on one option costs N*N '
            'credits.'),
    )
    is_open = models.BooleanField(
        default=True,
        verbose_name=_('Open for voting'),
        help_text=_(
            'Results are hidden from participants while a round is open, '
            'to avoid influencing later votes.'),
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.title


class Option(models.Model):
    voting_round = models.ForeignKey(
        VotingRound, on_delete=models.CASCADE, related_name='options')
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = models.TextField(blank=True,
                                   verbose_name=_('Description'))
    weight = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('weight', 'id')

    def __str__(self):
        return self.title


class Allocation(models.Model):
    """One participant's votes on one option within a round."""

    option = models.ForeignKey(
        Option, on_delete=models.CASCADE, related_name='allocations')
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quadratic_vote_allocations',
    )
    votes = models.IntegerField(default=0)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('option', 'creator')

    def __str__(self):
        return '{}: {} votes on {}'.format(
            self.creator_id, self.votes, self.option_id)
