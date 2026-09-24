import unittest
from datetime import datetime
from datetime import timedelta

from apps.pushnotifications import engine


def _dt(hours_from_now, now):
    return now + timedelta(hours=hours_from_now)


class PhasesEndingSoonTests(unittest.TestCase):

    def setUp(self):
        self.now = datetime(2026, 1, 1, 12, 0, 0)

    def test_phase_ending_within_window_matches(self):
        phase = engine.PhaseWindow(1, _dt(5, self.now))
        result = engine.phases_ending_soon([phase], self.now, window_hours=24)
        self.assertEqual(result, [phase])

    def test_phase_ending_after_window_does_not_match(self):
        phase = engine.PhaseWindow(1, _dt(48, self.now))
        result = engine.phases_ending_soon([phase], self.now, window_hours=24)
        self.assertEqual(result, [])

    def test_phase_that_already_ended_does_not_match(self):
        phase = engine.PhaseWindow(1, _dt(-1, self.now))
        result = engine.phases_ending_soon([phase], self.now, window_hours=24)
        self.assertEqual(result, [])

    def test_phase_ending_exactly_at_now_does_not_match(self):
        phase = engine.PhaseWindow(1, self.now)
        result = engine.phases_ending_soon([phase], self.now, window_hours=24)
        self.assertEqual(result, [])

    def test_phase_ending_exactly_at_window_boundary_matches(self):
        phase = engine.PhaseWindow(1, _dt(24, self.now))
        result = engine.phases_ending_soon([phase], self.now, window_hours=24)
        self.assertEqual(result, [phase])

    def test_phase_with_no_end_date_never_matches(self):
        phase = engine.PhaseWindow(1, None)
        result = engine.phases_ending_soon([phase], self.now, window_hours=24)
        self.assertEqual(result, [])

    def test_multiple_phases_only_matching_ones_returned(self):
        soon = engine.PhaseWindow(1, _dt(2, self.now))
        far = engine.PhaseWindow(2, _dt(72, self.now))
        result = engine.phases_ending_soon(
            [soon, far], self.now, window_hours=24)
        self.assertEqual(result, [soon])

    def test_non_positive_window_raises(self):
        with self.assertRaises(ValueError):
            engine.phases_ending_soon([], self.now, window_hours=0)


class BuildPayloadTests(unittest.TestCase):

    def test_includes_all_fields(self):
        payload = engine.build_payload(
            'phase.ending_soon', 'Ending soon', 'The phase ends in 24h',
            'https://example.test/project')
        self.assertEqual(payload, {
            'type': 'phase.ending_soon',
            'title': 'Ending soon',
            'body': 'The phase ends in 24h',
            'url': 'https://example.test/project',
        })


class ShouldPruneSubscriptionTests(unittest.TestCase):

    def test_404_prunes(self):
        self.assertTrue(engine.should_prune_subscription(404))

    def test_410_prunes(self):
        self.assertTrue(engine.should_prune_subscription(410))

    def test_500_does_not_prune(self):
        self.assertFalse(engine.should_prune_subscription(500))

    def test_200_does_not_prune(self):
        self.assertFalse(engine.should_prune_subscription(200))


if __name__ == '__main__':
    unittest.main()
