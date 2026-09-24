"""Unit tests for the pure-Python forecasting/Brier-scoring engine.

No Django involved -- runs with a bare ``python -m unittest``.
"""

import unittest

from apps.forecasting import engine


class BrierScoreTests(unittest.TestCase):

    def test_perfect_confident_forecast_scores_zero(self):
        self.assertEqual(engine.brier_score(1.0, 1), 0.0)
        self.assertEqual(engine.brier_score(0.0, 0), 0.0)

    def test_maximally_wrong_confident_forecast_scores_one(self):
        self.assertEqual(engine.brier_score(1.0, 0), 1.0)
        self.assertEqual(engine.brier_score(0.0, 1), 1.0)

    def test_maximally_uncertain_forecast_scores_quarter(self):
        self.assertAlmostEqual(engine.brier_score(0.5, 1), 0.25)
        self.assertAlmostEqual(engine.brier_score(0.5, 0), 0.25)

    def test_score_improves_the_closer_to_the_truth(self):
        # A forecaster who said 90% for something that happened should
        # score better than one who said 60%.
        confident = engine.brier_score(0.9, 1)
        unsure = engine.brier_score(0.6, 1)
        self.assertLess(confident, unsure)


class AggregateForecastTests(unittest.TestCase):

    def test_empty_input_returns_none(self):
        self.assertIsNone(engine.aggregate_forecast([]))

    def test_single_forecast_is_itself(self):
        self.assertEqual(engine.aggregate_forecast([0.7]), 0.7)

    def test_averages_multiple_forecasts(self):
        self.assertAlmostEqual(
            engine.aggregate_forecast([0.2, 0.4, 0.6, 0.8]), 0.5)

    def test_crowd_can_be_better_calibrated_than_any_individual(self):
        # Classic wisdom-of-crowds shape: two confident-but-wrong-ish
        # forecasters on opposite sides average out closer to a coin
        # flip than either extreme was.
        crowd = engine.aggregate_forecast([0.9, 0.1])
        self.assertAlmostEqual(crowd, 0.5)


class LeaderboardTests(unittest.TestCase):

    def test_empty_input_returns_empty(self):
        self.assertEqual(engine.leaderboard([]), [])

    def test_better_calibrated_forecaster_ranks_first(self):
        rows = [
            ('good', 0.9, 1),   # brier = 0.01
            ('bad', 0.5, 0),    # brier = 0.25
        ]
        board = engine.leaderboard(rows)
        self.assertEqual([r.forecaster_id for r in board], ['good', 'bad'])

    def test_scores_average_across_multiple_questions(self):
        rows = [
            ('alice', 1.0, 1),   # brier = 0.0
            ('alice', 0.0, 1),   # brier = 1.0
            # mean = 0.5
            ('bob', 0.5, 1),     # brier = 0.25
            ('bob', 0.5, 0),     # brier = 0.25
            # mean = 0.25
        ]
        board = engine.leaderboard(rows)
        by_id = {r.forecaster_id: r for r in board}
        self.assertAlmostEqual(by_id['alice'].mean_brier_score, 0.5)
        self.assertAlmostEqual(by_id['bob'].mean_brier_score, 0.25)
        self.assertEqual(by_id['alice'].n_questions, 2)
        # bob is better calibrated on average, so ranks first
        self.assertEqual([r.forecaster_id for r in board], ['bob', 'alice'])


if __name__ == '__main__':
    unittest.main()
