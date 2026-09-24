"""Pure-Python core for push notifications: which phases have just
entered "ending soon" and deserve a deadline reminder, and the shape of
the message sent to a subscriber's browser.

The actual delivery (Web Push encryption, VAPID signing, retry
scheduling against a browser's push endpoint) is Django/network-facing
and lives in services.py; retry backoff itself is not duplicated here
-- it reuses ``apps.webhooks.engine.should_retry`` /
``retry_delay_seconds``, since "wait longer after each failure, give up
eventually" is exactly the same problem for a webhook endpoint and a
push endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class PhaseWindow:
    phase_id: int
    end_date: object  # a datetime; kept generic so this stays Django-free


def phases_ending_soon(phases, now, window_hours=24):
    """Which of ``phases`` (an iterable of ``PhaseWindow``) end within
    ``window_hours`` of ``now`` but haven't ended yet -- the set that
    deserves a "this phase is ending soon" reminder right now.

    A phase with no ``end_date`` never matches (open-ended phases have
    nothing to remind about). Already-sent reminders are tracked
    separately (see ``PhaseReminderSent`` in models.py) -- this
    function only answers "is now the right time", not "was this
    already sent".
    """
    if window_hours <= 0:
        raise ValueError('window_hours must be positive')
    deadline = now + timedelta(hours=window_hours)
    return [
        phase for phase in phases
        if phase.end_date is not None
        and now < phase.end_date <= deadline
    ]


def build_payload(event_type, title, body, url):
    """The JSON body of the actual push message shown to the user.
    Kept small and flat -- the whole encrypted Web Push payload has a
    practical size limit (~4KB after encryption overhead), and a push
    notification is a prompt to visit the site, not the content
    itself.
    """
    return {
        'type': event_type,
        'title': title,
        'body': body,
        'url': url,
    }


def should_prune_subscription(status_code):
    """A 404 or 410 response from a push endpoint means the browser
    subscription is permanently gone (uninstalled, revoked, expired) --
    no amount of retrying will ever succeed, so the subscription should
    be deleted rather than scheduled for retry.
    """
    return status_code in (404, 410)
