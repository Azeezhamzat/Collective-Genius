import secrets

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

EVENT_CHOICES = (
    ('report.created', _('A comment was reported')),
    ('consent_proposal.created', _('A consent proposal was submitted')),
    ('forecasting_question.created', _('A forecasting question was added')),
    ('synthesis_snapshot.created', _('A synthesis run completed')),
)


def _generate_secret():
    return secrets.token_hex(32)


class Endpoint(models.Model):
    """A URL a third-party integration (Slack, Zapier, a custom
    dashboard) registered to receive event notifications for one
    organisation."""

    organisation = models.ForeignKey(
        settings.A4_ORGANISATIONS_MODEL,
        on_delete=models.CASCADE,
        related_name='webhook_endpoints',
    )
    url = models.URLField(verbose_name=_('Endpoint URL'))
    secret = models.CharField(
        max_length=64, default=_generate_secret, editable=False,
        help_text=_(
            'Used to sign delivered payloads (HMAC-SHA256, hex-encoded, '
            'sent as the X-Webhook-Signature header) so the receiver '
            'can verify a delivery really came from here.'),
    )
    event_types = models.JSONField(
        default=list, blank=True,
        verbose_name=_('Event types'),
        help_text=_('Which events to send. Empty means every event '
                    'type.'),
    )
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.url

    def wants(self, event_type):
        return not self.event_types or event_type in self.event_types


class Delivery(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = (
        (STATUS_PENDING, _('Pending')),
        (STATUS_SUCCESS, _('Success')),
        (STATUS_FAILED, _('Failed (retries exhausted)')),
    )

    endpoint = models.ForeignKey(
        Endpoint, on_delete=models.CASCADE, related_name='deliveries')
    event_type = models.CharField(max_length=100)
    data = models.JSONField()
    attempt_number = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    response_status = models.PositiveIntegerField(null=True, blank=True)
    error = models.TextField(blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return '{} -> {} ({})'.format(
            self.event_type, self.endpoint_id, self.status)
