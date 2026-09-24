"""Pure-Python core for two trust & safety mechanisms: rate limiting
(a token bucket) and a lightweight spam-likelihood heuristic for
user-submitted text.

Both are deliberately simple, explainable algorithms rather than a
learned model: a token bucket is the standard, well-understood way to
allow bursts while capping sustained rate, and the spam heuristic is a
small set of legible signals (link density, repeated characters,
shouting, a link with almost no other text) rather than an opaque
score nobody can audit or explain to someone who got flagged. Both are
unit tested standalone, no Django involved.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field


@dataclass
class TokenBucket:
    """Allows bursts up to ``capacity``, then refills at
    ``refill_rate`` tokens per second. ``tokens``/``last_refill_at``
    are the bucket's current state -- callers persist these between
    calls (e.g. in a cache), this class has no storage of its own.
    """

    capacity: float
    tokens: float
    refill_rate: float
    last_refill_at: float

    def _refill(self, now):
        elapsed = max(0.0, now - self.last_refill_at)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill_at = now

    def consume(self, now, amount=1.0):
        """Try to consume ``amount`` tokens at time ``now``. Always
        refills first (so waiting time is never wasted even on a
        rejected request), then returns True and deducts the tokens if
        there were enough, or False (deducting nothing) if not.
        """
        self._refill(now)
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


def new_bucket(capacity, refill_rate, now):
    """A fresh, full bucket -- what a rate limiter creates the first
    time it sees a new key (a user, an IP)."""
    return TokenBucket(capacity=capacity, tokens=capacity,
                       refill_rate=refill_rate, last_refill_at=now)


_URL_RE = re.compile(r'https?://\S+')
_REPEATED_CHAR_RE = re.compile(r'(.)\1{4,}')  # same character 5+ times running


@dataclass
class SpamScore:
    score: float  # 0.0 (looks fine) .. 1.0 (very spam-like)
    reasons: list = field(default_factory=list)


def score_text(text):
    """Score a piece of user-submitted text for spam-likelihood.

    This is advisory, not a filter: nothing here blocks a submission,
    it's meant to flag things for a moderator to look at (see
    apps/trustsafety/signals.py, which sets an existing comment
    moderation flag rather than rejecting the comment outright) --
    false positives should cost a moderator a glance, not silently
    censor a real participant.
    """
    text = text or ''
    words = text.split()
    urls = _URL_RE.findall(text)
    non_url_words = [w for w in words if not _URL_RE.match(w)]
    reasons = []
    score = 0.0

    if non_url_words:
        link_ratio = len(urls) / len(non_url_words)
        if link_ratio > 0.3:
            score += 0.4
            reasons.append('high link-to-word ratio')

    if len(urls) >= 3:
        score += 0.3
        reasons.append('multiple links')

    if _REPEATED_CHAR_RE.search(text):
        score += 0.2
        reasons.append('repeated characters')

    letters = [c for c in text if c.isalpha()]
    if len(text) > 20 and letters:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio > 0.6:
            score += 0.2
            reasons.append('excessive capitalization')

    if urls and len(non_url_words) <= 3:
        score += 0.3
        reasons.append('very short message dominated by a link')

    return SpamScore(score=min(score, 1.0), reasons=reasons)


def is_likely_spam(text, threshold=0.5):
    return score_text(text).score >= threshold
