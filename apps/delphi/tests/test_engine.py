"""Unit tests for the pure-Python Delphi round-aggregation and
convergence engine.

No Django involved -- runs with a bare ``python -m unittest``.
"""

import unittest

from apps.delphi import engine


class AggregateRoundTests(unittest.TestCase):

    def test_empty_values_returns_none(self):
        self.assertIsNone(engine.aggregate_round(1, []))

    def test_single_value_has_zero_spread(self):
        stats = engine.aggregate_round(1, [42])
        self.assertEqual(stats.n_responses, 1)
        self.assertEqual(stats.median, 42)
        self.assertEqual(stats.mean, 42)
        self.assertEqual(stats.stdev, 0.0)
        self.assertEqual(stats.minimum, 42)
        self.assertEqual(stats.maximum, 42)

    def test_basic_statistics_are_correct(self):
        stats = engine.aggregate_round(2, [10, 20, 30, 40, 50])
        self.assertEqual(stats.round_number, 2)
        self.assertEqual(stats.n_responses, 5)
        self.assertEqual(stats.median, 30)
        self.assertEqual(stats.mean, 30)
        self.assertEqual(stats.minimum, 10)
        self.assertEqual(stats.maximum, 50)
        self.assertGreater(stats.stdev, 0)

    def test_wide_spread_has_higher_stdev_than_narrow_spread(self):
        narrow = engine.aggregate_round(1, [48, 49, 50, 51, 52])
        wide = engine.aggregate_round(1, [10, 30, 50, 70, 90])
        self.assertLess(narrow.stdev, wide.stdev)


class HasConvergedTests(unittest.TestCase):

    def test_fewer_than_two_rounds_has_not_converged(self):
        one_round = [engine.aggregate_round(1, [10, 50, 90])]
        self.assertFalse(engine.has_converged(one_round))
        self.assertFalse(engine.has_converged([]))

    def test_spread_tightening_a_lot_counts_as_converged(self):
        rounds = [
            engine.aggregate_round(1, [10, 30, 50, 70, 90]),  # wide
            engine.aggregate_round(2, [45, 48, 50, 52, 55]),  # tight
        ]
        self.assertTrue(engine.has_converged(rounds))

    def test_spread_barely_changing_has_not_converged(self):
        rounds = [
            engine.aggregate_round(1, [10, 30, 50, 70, 90]),
            engine.aggregate_round(2, [15, 35, 50, 65, 85]),
        ]
        self.assertFalse(engine.has_converged(rounds))

    def test_spread_widening_has_not_converged(self):
        rounds = [
            engine.aggregate_round(1, [45, 48, 50, 52, 55]),
            engine.aggregate_round(2, [10, 30, 50, 70, 90]),
        ]
        self.assertFalse(engine.has_converged(rounds))

    def test_zero_spread_in_first_round_is_never_converged(self):
        # Everyone already agreed round one -- nothing for the process
        # to have converged *through*.
        rounds = [
            engine.aggregate_round(1, [50, 50, 50]),
            engine.aggregate_round(2, [50, 50, 50]),
        ]
        self.assertFalse(engine.has_converged(rounds))

    def test_empty_rounds_are_skipped(self):
        rounds = [
            engine.aggregate_round(1, [10, 30, 50, 70, 90]),
            engine.aggregate_round(2, []),  # nobody responded this round
            engine.aggregate_round(3, [45, 48, 50, 52, 55]),
        ]
        self.assertTrue(engine.has_converged(rounds))

    def test_custom_threshold_ratio(self):
        rounds = [
            engine.aggregate_round(1, [0, 100]),   # stdev = 50
            engine.aggregate_round(2, [40, 60]),   # stdev = 10
        ]
        # 10 / 50 = 0.2, so a threshold of 0.5 should count as converged...
        self.assertTrue(engine.has_converged(rounds, threshold_ratio=0.5))
        # ...but a much stricter threshold should not.
        self.assertFalse(engine.has_converged(rounds, threshold_ratio=0.1))


if __name__ == '__main__':
    unittest.main()
