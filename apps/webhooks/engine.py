"""Pure-Python core for outbound webhooks: payload signing/verification,
and retry-backoff scheduling.

Both pieces are exactly the kind of logic worth testing directly even
though the surrounding Django/HTTP machinery can't be exercised in this
sandbox:

* **Signing** is genuinely security-sensitive. A receiver's whole
  ability to trust a webhook payload came from *this platform* (and not
  an attacker who guessed or leaked the endpoint URL) depends on the
  signature being computed correctly and compared in constant time.
  Getting this subtly wrong is exactly the kind of bug that looks fine
  in review and is a real vulnerability in production, so it's the part
  most worth a test proving it, not just eyeballing it.
* **Retry scheduling** decides whether a real integration (someone's
  Slack notifier, their Zapier hook) gets the event at all if the first
  delivery attempt fails -- a receiver that's briefly down shouldn't
  mean an event is silently dropped, but a permanently-dead endpoint
  shouldn't be retried forever either.
"""

from __future__ import annotations

import hashlib
import hmac
import json


def canonical_payload(event_type, data):
    """A deterministic JSON encoding of an event, used as both what
    gets sent and what gets signed -- signing anything other than
    exactly the bytes that get transmitted would let a receiver's
    signature check pass on tampered data.
    """
    return json.dumps(
        {'event': event_type, 'data': data},
        sort_keys=True, separators=(',', ':'),
    ).encode('utf-8')


def sign(payload_bytes, secret):
    """HMAC-SHA256 signature of ``payload_bytes``, as a hex digest."""
    return hmac.new(
        secret.encode('utf-8'), payload_bytes, hashlib.sha256
    ).hexdigest()


def verify(payload_bytes, secret, signature):
    """Constant-time-safe check that ``signature`` matches
    ``payload_bytes`` signed with ``secret`` -- what a receiver should
    do, and what this platform's own delivery code relies on being
    correct. Uses ``hmac.compare_digest`` rather than ``==`` so a
    receiver's comparison can't be timed to leak the correct signature
    byte by byte.
    """
    expected = sign(payload_bytes, secret)
    return hmac.compare_digest(expected, signature)


# Exponential backoff: 1 min, 5 min, 30 min, 2 hours, 12 hours -- then
# give up. Chosen to recover quickly from a brief blip (a receiver
# restarting) without hammering an endpoint that's actually down, and to
# stop eventually rather than retrying a dead URL forever.
RETRY_SCHEDULE_SECONDS = (60, 300, 1800, 7200, 43200)


def should_retry(attempt_number):
    """``attempt_number`` is 1 for the first (original) delivery
    attempt. True if there's another retry left in the schedule after
    this attempt failed.
    """
    return attempt_number <= len(RETRY_SCHEDULE_SECONDS)


def retry_delay_seconds(attempt_number):
    """Seconds to wait before retrying after ``attempt_number`` has
    failed. Raises IndexError if ``should_retry(attempt_number)`` is
    False -- callers should check that first.
    """
    return RETRY_SCHEDULE_SECONDS[attempt_number - 1]
