"""Rate-limiting middleware: caps how many POST requests one user (or,
for anonymous requests, one IP) can make in a rolling window, using the
token-bucket algorithm in engine.py.

Bucket state is stored in Django's cache framework -- works with
whatever CACHES backend a deployment already has configured (the
default LocMemCache is fine for a single-process deployment; a real
multi-worker deployment should use a shared backend like Redis/
Memcached for the limit to actually be shared across workers, same as
any other cache-backed rate limiter).

Off by default (see settings.A4_RATE_LIMIT_ENABLED) -- this is
middleware that runs on every request, so it stays inert until a
deployment opts in, rather than risking blocking legitimate traffic on
a default nobody chose.
"""

import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

from . import engine

CACHE_KEY_PREFIX = 'a4_candy_trustsafety:rate_limit:'


def _client_key(request):
    if request.user.is_authenticated:
        return 'user:{}'.format(request.user.pk)
    return 'ip:{}'.format(request.META.get('REMOTE_ADDR', 'unknown'))


class RateLimitMiddleware:
    """Limits POST requests per client. GET/HEAD/OPTIONS are never
    limited -- this is about write actions (submitting a comment,
    casting a vote, adding a proposal), not browsing.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (getattr(settings, 'A4_RATE_LIMIT_ENABLED', False)
                and request.method == 'POST'
                and not self._allow(request)):
            return JsonResponse(
                {'error': 'Too many requests. Please slow down and try '
                          'again shortly.'},
                status=429,
            )
        return self.get_response(request)

    def _allow(self, request):
        capacity = getattr(settings, 'A4_RATE_LIMIT_CAPACITY', 30)
        refill_rate = getattr(settings, 'A4_RATE_LIMIT_REFILL_PER_SECOND',
                              30 / 60)  # 30 requests per minute, by default

        key = CACHE_KEY_PREFIX + _client_key(request)
        now = time.time()
        state = cache.get(key)

        if state is None:
            bucket = engine.new_bucket(capacity, refill_rate, now)
        else:
            bucket = engine.TokenBucket(
                capacity=capacity, tokens=state['tokens'],
                refill_rate=refill_rate, last_refill_at=state['last_refill_at'])

        allowed = bucket.consume(now)
        cache.set(
            key,
            {'tokens': bucket.tokens, 'last_refill_at': bucket.last_refill_at},
            timeout=3600,
        )
        return allowed
