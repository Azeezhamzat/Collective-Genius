"""Unit tests for the pure-Python activity-bucketing helpers.

No Django involved -- runs with a bare ``python -m unittest``.
"""

import unittest
from datetime import datetime
from datetime import timedelta
from datetime import timezone as dt_timezone

from apps.facilitator import engine

NOW = datetime(2024, 6, 15, 12, 0, 0, tzinfo=dt_timezone.utc)


def days_ago(n, hour=10):
    return (NOW - timedelta(days=n)).replace(hour=hour, minute=0, second=0,
                                             microsecond=0)


class BucketByDayTests(unittest.TestCase):

    def test_empty_input_still_returns_full_window_of_zeros(self):
        buckets = engine.bucket_by_day([], now=NOW, days=7)
        self.assertEqual(len(buckets), 7)
        self.assertTrue(all(b.count == 0 for b in buckets))

    def test_buckets_are_oldest_first(self):
        buckets = engine.bucket_by_day([], now=NOW, days=3)
        dates = [b.date for b in buckets]
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(dates[-1], NOW.date())

    def test_counts_land_on_the_right_day(self):
        timestamps = [days_ago(0), days_ago(0), days_ago(1), days_ago(2)]
        buckets = engine.bucket_by_day(timestamps, now=NOW, days=7)
        by_date = {b.date: b.count for b in buckets}
        self.assertEqual(by_date[NOW.date()], 2)
        self.assertEqual(by_date[NOW.date() - timedelta(days=1)], 1)
        self.assertEqual(by_date[NOW.date() - timedelta(days=2)], 1)
        self.assertEqual(by_date[NOW.date() - timedelta(days=3)], 0)

    def test_timestamp_exactly_at_window_edge_is_included(self):
        # days=7 means today + 6 days back = 7 days total.
        edge = days_ago(6)
        buckets = engine.bucket_by_day([edge], now=NOW, days=7)
        by_date = {b.date: b.count for b in buckets}
        self.assertEqual(by_date[NOW.date() - timedelta(days=6)], 1)

    def test_timestamp_just_outside_window_is_excluded(self):
        outside = days_ago(7)
        buckets = engine.bucket_by_day([outside], now=NOW, days=7)
        self.assertEqual(sum(b.count for b in buckets), 0)

    def test_future_timestamp_is_ignored(self):
        future = NOW + timedelta(days=1)
        buckets = engine.bucket_by_day([future], now=NOW, days=7)
        self.assertEqual(sum(b.count for b in buckets), 0)


class TotalInWindowTests(unittest.TestCase):

    def test_sums_all_buckets(self):
        timestamps = [days_ago(0), days_ago(1), days_ago(1), days_ago(10)]
        total = engine.total_in_window(timestamps, now=NOW, days=7)
        self.assertEqual(total, 3)  # the 10-days-ago one is out of window

    def test_empty_input_is_zero(self):
        self.assertEqual(engine.total_in_window([], now=NOW), 0)


if __name__ == '__main__':
    unittest.main()
