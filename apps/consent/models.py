from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from adhocracy4.modules import models as module_models


class Proposal(models.Model):
    """Something a group member proposes the group do, to be decided by
    consent rather than a majority vote."""

    module = models.ForeignKey(
        module_models.Module,
        on_delete=models.CASCADE,
        related_name='consent_proposals',
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consent_proposals',
    )
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = models.TextField(verbose_name=_('Description'))
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.title

    @property
    def project(self):
        return self.module.project


class Response(models.Model):
    AGREE = 'agree'
    STAND_ASIDE = 'stand_aside'
    OBJECT = 'object'
    STANCE_CHOICES = (
        (AGREE, _('Agree')),
        (STAND_ASIDE, _("Stand aside (won't block, doesn't support)")),
        (OBJECT, _('Object (blocks the proposal until resolved)')),
    )

    proposal = models.ForeignKey(
        Proposal, on_delete=models.CASCADE, related_name='responses')
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consent_responses',
    )
    stance = models.CharField(max_length=16, choices=STANCE_CHOICES)
    reason = models.TextField(
        blank=True,
        verbose_name=_('Reason'),
        help_text=_('Required for an objection -- what would need to '
                    'change for you to withdraw it?'),
    )
    resolved = models.BooleanField(
        default=False,
        verbose_name=_('Resolved'),
        help_text=_(
            'Only meaningful for an objection: has it been addressed? '
            'The proposer (or the objector themselves) can mark it '
            'resolved once it no longer stands in the way.'),
    )
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('proposal', 'creator')

    def __str__(self):
        return '{}: {} on {}'.format(
            self.creator_id, self.stance, self.proposal_id)
