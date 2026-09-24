from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from adhocracy4.modules import models as module_models


class Question(models.Model):
    """A yes/no question with a checkable resolution criterion that
    participants forecast a probability for."""

    module = models.ForeignKey(
        module_models.Module,
        on_delete=models.CASCADE,
        related_name='forecasting_questions',
    )
    title = models.CharField(max_length=255, verbose_name=_('Question'))
    resolution_criteria = models.TextField(
        blank=True,
        verbose_name=_('Resolution criteria'),
        help_text=_(
            'How will it be decided, objectively, whether this '
            'resolves yes or no? Vague criteria make the forecasts '
            'meaningless.'),
    )
    closes_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('Forecasting closes at'),
        help_text=_(
            'After this date, forecasts can no longer be submitted or '
            'changed. Leave blank to allow forecasts until resolution.'),
    )
    is_resolved = models.BooleanField(default=False,
                                      verbose_name=_('Resolved'))
    outcome = models.BooleanField(
        null=True, blank=True,
        verbose_name=_('Outcome'),
        help_text=_('Only meaningful once resolved: did it happen?'),
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.title

    @property
    def project(self):
        return self.module.project


class Forecast(models.Model):
    """One participant's probability estimate for a Question, as a
    whole-number percentage (0-100)."""

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='forecasts')
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forecasts',
    )
    probability = models.PositiveSmallIntegerField(
        verbose_name=_('Probability (%)'))
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('question', 'creator')

    def __str__(self):
        return '{}: {}% on {}'.format(
            self.creator_id, self.probability, self.question_id)
