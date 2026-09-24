"""Pure-Python helpers for the facilitator toolkit's activity summary.

No Django dependency: date-bucketing is easy to get subtly wrong
(timezone handling, off-by-one on day boundaries), so it's isolated
here and unit tested with plain datetimes rather than live comment
data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from datetime import timezone as dt_timezone


@dataclass
class DayCount:
    date: object  # datetime.date
    count: int


def bucket_by_day(timestamps, now=None, days=7):
    """Count how many ``timestamps`` fall on each of the last ``days``
    days (including today), oldest day first.

    ``timestamps``: iterable of datetimes, all consistently timezone-aware
    or all naive, matching ``now``'s awareness (mixing the two raises a
    TypeError from the stdlib comparison, same as comparing them
    directly). Timestamps older than the window, or after ``now``, are
    ignored.
    """
    if now is None:
        now = datetime.now(dt_timezone.utc)

    today = now.date()
    window_start = today - timedelta(days=days - 1)

    counts = {today - timedelta(days=i): 0 for i in range(days)}
    for ts in timestamps:
        day = ts.date()
        if window_start <= day <= today:
            counts[day] += 1

    return [DayCount(date=day, count=counts[day]) for day in sorted(counts)]


def total_in_window(timestamps, now=None, days=7):
    return sum(d.count for d in bucket_by_day(timestamps, now=now,
                                              days=days))
