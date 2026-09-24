from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from adhocracy4.modules import models as module_models


class DelegationRound(models.Model):
    """A liquid-democracy decision: a fixed set of options a
    participant either votes on directly or delegates their vote for,
    transitively, to someone they trust."""

    module = models.ForeignKey(
        module_models.Module,
        on_delete=models.CASCADE,
        related_name='delegation_rounds',
    )
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = models.TextField(blank=True,
                                   verbose_name=_('Description'))
    is_open = models.BooleanField(
        default=True,
        verbose_name=_('Open for voting/delegating'),
        help_text=_(
            'Results are hidden from participants while a round is '
            'open, to avoid influencing later votes and delegations.'),
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.title

    @property
    def project(self):
        return self.module.project


class Option(models.Model):
    delegation_round = models.ForeignKey(
        DelegationRound, on_delete=models.CASCADE, related_name='options')
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = models.TextField(blank=True,
                                   verbose_name=_('Description'))
    weight = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('weight', 'id')

    def __str__(self):
        return self.title


class Vote(models.Model):
    """One participant's direct vote in a round. A participant who has
    a Delegation on file for this round instead has no Vote row --
    casting one (see ``services.cast_vote``) deletes any existing
    Delegation for the same round, since voting directly always
    supersedes a standing delegation, never coexists with it.
    """

    delegation_round = models.ForeignKey(
        DelegationRound, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(
        Option, on_delete=models.CASCADE, related_name='votes')
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delegation_votes',
    )
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('delegation_round', 'creator')

    def __str__(self):
        return '{}: voted for {}'.format(self.creator_id, self.option_id)


class Delegation(models.Model):
    """One participant's standing delegation of their vote, for one
    round, to another participant. Revocable at any time by casting a
    direct Vote instead, or by deleting this row -- both leave the
    delegator's vote unresolved (abstaining) rather than silently
    reassigning it anywhere."""

    delegation_round = models.ForeignKey(
        DelegationRound, on_delete=models.CASCADE,
        related_name='delegations')
    delegator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delegations_given',
    )
    delegatee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delegations_received',
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('delegation_round', 'delegator')

    def __str__(self):
        return '{} -> {} on round {}'.format(
            self.delegator_id, self.delegatee_id, self.delegation_round_id)
