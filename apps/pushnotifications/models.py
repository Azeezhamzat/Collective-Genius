from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

EVENT_CHOICES = (
    ('synthesis_snapshot.created', _('A synthesis run completed')),
    ('phase.ending_soon', _('A phase is ending soon')),
)


class PushSubscription(models.Model):
    """One browser's Web Push subscription for one user, on one
    project. A user can follow (and so get notified about) several
    projects, and can have several subscriptions if they use more than
    one browser/device -- both are normal, not an error case.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
    )
    project = models.ForeignKey(
        'a4projects.Project',
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
    )
    endpoint = models.URLField(max_length=1024, unique=True)
    p256dh_key = models.CharField(max_length=255)
    auth_key = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return '{} on {}'.format(self.user, self.project)

    def to_subscription_info(self):
        return {
            'endpoint': self.endpoint,
            'keys': {
                'p256dh': self.p256dh_key,
                'auth': self.auth_key,
            },
        }


class PushDelivery(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = (
        (STATUS_PENDING, _('Pending')),
        (STATUS_SUCCESS, _('Success')),
        (STATUS_FAILED, _('Failed (retries exhausted)')),
    )

    subscription = models.ForeignKey(
        PushSubscription, on_delete=models.CASCADE,
        related_name='deliveries')
    event_type = models.CharField(max_length=100, choices=EVENT_CHOICES)
    payload = models.JSONField()
    attempt_number = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error = models.TextField(blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return '{} -> {} ({})'.format(
            self.event_type, self.subscription_id, self.status)


class PhaseReminderSent(models.Model):
    """One row per phase a deadline reminder has already been sent
    for, so ``send_phase_deadline_reminders`` (run periodically, see
    the management command) never notifies the same phase's followers
    twice."""

    phase = models.OneToOneField(
        'a4phases.Phase', on_delete=models.CASCADE,
        related_name='push_reminder_sent')
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'reminder sent for phase {}'.format(self.phase_id)
