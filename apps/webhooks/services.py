"""Bridges the real Endpoint/Delivery models to the pure-Python signing
engine, and does the actual HTTP delivery.

Uses the standard library's ``urllib.request`` rather than adding
``requests`` as a new dependency -- webhook delivery should work with
no extra install, unlike the optional LLM backends elsewhere in this
project.
"""

import logging
import urllib.error
import urllib.request
from datetime import timedelta

from django.utils import timezone

from . import engine
from .models import Delivery

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 10


def dispatch_event(organisation, event_type, data):
    """Create (and immediately attempt) a Delivery for every active
    Endpoint of ``organisation`` that wants ``event_type``.

    Never raises: a broken or slow receiver must not break whatever
    action in the platform triggered this event.
    """
    endpoints = organisation.webhook_endpoints.filter(is_active=True)
    for endpoint in endpoints:
        if not endpoint.wants(event_type):
            continue
        delivery = Delivery.objects.create(
            endpoint=endpoint, event_type=event_type, data=data)
        try:
            attempt_delivery(delivery)
        except Exception:
            logger.exception(
                'Unexpected error dispatching webhook delivery %s',
                delivery.pk)


def attempt_delivery(delivery):
    """Try to deliver ``delivery`` now. Updates its status in place:
    success, scheduled for retry, or permanently failed once the retry
    schedule is exhausted.
    """
    payload = engine.canonical_payload(delivery.event_type, delivery.data)
    signature = engine.sign(payload, delivery.endpoint.secret)

    request = urllib.request.Request(
        delivery.endpoint.url,
        data=payload,
        method='POST',
        headers={
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-Webhook-Event': delivery.event_type,
        },
    )

    try:
        with urllib.request.urlopen(
                request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            delivery.response_status = response.status
            if 200 <= response.status < 300:
                delivery.status = Delivery.STATUS_SUCCESS
                delivery.next_retry_at = None
                delivery.save(update_fields=[
                    'response_status', 'status', 'next_retry_at',
                    'modified'])
                return
            _schedule_retry_or_fail(
                delivery,
                error='Endpoint responded with status {}'.format(
                    response.status),
            )
    except urllib.error.HTTPError as err:
        delivery.response_status = err.code
        _schedule_retry_or_fail(delivery, error=str(err))
    except (urllib.error.URLError, OSError, ValueError) as err:
        _schedule_retry_or_fail(delivery, error=str(err))


def _schedule_retry_or_fail(delivery, error):
    delivery.error = error
    if engine.should_retry(delivery.attempt_number):
        delay = engine.retry_delay_seconds(delivery.attempt_number)
        delivery.next_retry_at = timezone.now() + timedelta(seconds=delay)
        delivery.status = Delivery.STATUS_PENDING
        delivery.save(update_fields=[
            'response_status', 'error', 'next_retry_at', 'status',
            'modified'])
    else:
        delivery.status = Delivery.STATUS_FAILED
        delivery.next_retry_at = None
        delivery.save(update_fields=[
            'response_status', 'error', 'next_retry_at', 'status',
            'modified'])


def retry_due_deliveries():
    """Re-attempt every pending Delivery whose retry time has passed.
    Meant to be called periodically (see management command
    ``send_webhook_retries``) -- this project has no task queue/beat
    scheduler configured, so a real deployment needs to run that
    command on a cron schedule (e.g. every few minutes) for retries to
    actually happen; nothing here does that on its own.
    """
    due = Delivery.objects.filter(
        status=Delivery.STATUS_PENDING,
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
                'Unexpected error retrying webhook delivery %s',
                delivery.pk)
