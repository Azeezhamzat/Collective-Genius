"""Bridges PushSubscription/PushDelivery to actual Web Push delivery.

Uses ``pywebpush`` (a required new dependency, see requirements/base.txt)
rather than hand-rolling the Web Push crypto (ECDH + HKDF + AES-128-GCM
payload encryption, ES256-signed VAPID JWTs) -- that's exactly the kind
of security-sensitive code that should never be reimplemented from
scratch when a well-established library already does it correctly.

Retry backoff is not duplicated from apps/webhooks: ``should_retry`` /
``retry_delay_seconds`` there are generic ("wait longer after each
failure, give up eventually"), so this reuses them directly.

Requires ``A4_VAPID_PUBLIC_KEY`` / ``A4_VAPID_PRIVATE_KEY`` to be
configured (see settings comment) -- until a deployment generates and
sets those, ``notifications_enabled()`` is False and nothing here
sends anything.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.webhooks import engine as retry_engine

from . import engine
from .models import PushDelivery
from .models import PushSubscription

logger = logging.getLogger(__name__)


def notifications_enabled():
    return bool(
        getattr(settings, 'A4_VAPID_PUBLIC_KEY', '')
        and getattr(settings, 'A4_VAPID_PRIVATE_KEY', ''))


def notify_project_followers(project, event_type, title, body, url):
    """Create (and immediately attempt) a PushDelivery for every push
    subscription registered for ``project``.

    Never raises: a broken subscription or an unreachable push service
    must not break whatever action triggered this notification.
    """
    if not notifications_enabled():
        return
    payload = engine.build_payload(event_type, title, body, url)
    subscriptions = PushSubscription.objects.filter(project=project)
    for subscription in subscriptions:
        delivery = PushDelivery.objects.create(
            subscription=subscription, event_type=event_type,
            payload=payload)
        try:
            attempt_delivery(delivery)
        except Exception:
            logger.exception(
                'Unexpected error dispatching push delivery %s',
                delivery.pk)


def attempt_delivery(delivery):
    """Try to deliver ``delivery`` now. Updates its status in place:
    success, scheduled for retry, permanently failed, or -- if the
    browser says the subscription is gone -- deletes the subscription
    outright (which cascades to delete this delivery too, so no
    further status update happens on it in that branch).
    """
    from pywebpush import WebPushException
    from pywebpush import webpush

    subscription = delivery.subscription
    try:
        webpush(
            subscription_info=subscription.to_subscription_info(),
            data=_encode(delivery.payload),
            vapid_private_key=settings.A4_VAPID_PRIVATE_KEY,
            vapid_claims={
                'sub': 'mailto:{}'.format(settings.A4_VAPID_ADMIN_EMAIL),
            },
            timeout=10,
        )
    except WebPushException as err:
        status_code = getattr(err.response, 'status_code', None)
        if status_code is not None and engine.should_prune_subscription(
                status_code):
            subscription.delete()
            return
        _schedule_retry_or_fail(delivery, error=str(err))
        return
    except Exception as err:
        _schedule_retry_or_fail(delivery, error=str(err))
        return

    delivery.status = PushDelivery.STATUS_SUCCESS
    delivery.next_retry_at = None
    delivery.save(update_fields=['status', 'next_retry_at', 'modified'])


def _encode(payload):
    import json
    return json.dumps(payload)


def _schedule_retry_or_fail(delivery, error):
    delivery.error = error
    if retry_engine.should_retry(delivery.attempt_number):
        delay = retry_engine.retry_delay_seconds(delivery.attempt_number)
        delivery.next_retry_at = timezone.now() + timedelta(seconds=delay)
        delivery.status = PushDelivery.STATUS_PENDING
    else:
        delivery.status = PushDelivery.STATUS_FAILED
        delivery.next_retry_at = None
    delivery.save(update_fields=[
        'error', 'next_retry_at', 'status', 'modified'])


def retry_due_deliveries():
    """Re-attempt every pending PushDelivery whose retry time has
    passed. Meant to run on a cron schedule (see the
    ``send_push_notification_retries`` management command) -- same
    reasoning as ``apps.webhooks.services.retry_due_deliveries``: this
    project has no task queue, so nothing calls this on its own.
    """
    due = PushDelivery.objects.filter(
        status=PushDelivery.STATUS_PENDING,
        next_retry_at__isnull=False,
        next_retry_at__lte=timezone.now(),
    )
    for delivery in due:
        delivery.attempt_number += 1
        delivery.save(update_fields=['attempt_number', 'modified'])
        try:
            attempt_delivery(delivery)
        except Exception:
            logger.exception(
                'Unexpected error retrying push delivery %s', delivery.pk)


def send_phase_deadline_reminders(window_hours=24):
    """Find phases ending within ``window_hours`` that haven't already
    had a reminder sent, notify each project's followers, and record
    that the reminder went out so this never double-sends. Meant to run
    on a cron schedule (e.g. hourly) -- see the
    ``send_phase_deadline_reminders`` management command.
    """
    from adhocracy4.phases.models import Phase

    from .models import PhaseReminderSent

    now = timezone.now()
    candidates = Phase.objects.filter(
        end_date__isnull=False,
        push_reminder_sent__isnull=True,
    ).select_related('module', 'module__project')

    windows = [
        engine.PhaseWindow(phase.pk, phase.end_date)
        for phase in candidates
    ]
    due_ids = {
        window.phase_id
        for window in engine.phases_ending_soon(
            windows, now, window_hours=window_hours)
    }
    if not due_ids:
        return

    for phase in candidates:
        if phase.pk not in due_ids:
            continue
        project = phase.module.project
        notify_project_followers(
            project, 'phase.ending_soon',
            title='{} is ending soon'.format(phase.name),
            body='The "{}" phase of {} ends soon.'.format(
                phase.name, project.name),
            url=project.get_absolute_url(),
        )
        PhaseReminderSent.objects.create(phase=phase)
