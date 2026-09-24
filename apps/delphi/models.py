from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from adhocracy4.modules import models as module_models


class Question(models.Model):
    """A numeric-estimate question for structured, anonymous, multi-round
    elicitation. Advancing ``current_round`` opens a new round; past
    rounds' responses are immutable once the round has moved on."""

    module = models.ForeignKey(
        module_models.Module,
        on_delete=models.CASCADE,
        related_name='delphi_questions',
    )
    title = models.CharField(max_length=255, verbose_name=_('Question'))
    description = models.TextField(blank=True,
                                   verbose_name=_('Description'))
    scale_hint = models.CharField(
        max_length=64, blank=True,
        verbose_name=_('Scale'),
        help_text=_('What unit is the estimate in? e.g. "0-100", '
                    '"years", "EUR". Shown next to the input field.'),
    )
    current_round = models.PositiveIntegerField(default=1)
    is_closed = models.BooleanField(
        default=False,
        verbose_name=_('Closed'),
        help_text=_('No more rounds will open once closed.'),
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.title

    @property
    def project(self):
        return self.module.project


class Response(models.Model):
    """One participant's estimate in one round. Anonymous by design:
    the platform tracks who submitted what (to enforce one response per
    participant per round and let them revise it while the round is
    open), but nothing about ``creator`` is ever shown to other
    participants -- only the round's aggregate is."""

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='responses')
    round_number = models.PositiveIntegerField()
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delphi_responses',
    )
    value = models.FloatField(verbose_name=_('Your estimate'))
    rationale = models.TextField(
        blank=True,
        verbose_name=_('Rationale (optional)'),
        help_text=_('Why this estimate? Shown anonymously alongside '
                    'the aggregate in the next round.'),
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('question', 'round_number', 'creator')
        ordering = ('round_number', 'id')

    def __str__(self):
        return '{}: {} in round {} of {}'.format(
            self.creator_id, self.value, self.round_number,
            self.question_id)
