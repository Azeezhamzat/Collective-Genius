"""Unit tests for the pure-Python moderation-flag diff.

No Django involved -- runs with a bare ``python -m unittest``.
"""

import unittest

from apps.moderationlog import engine


class DiffModerationFlagsTests(unittest.TestCase):

    def test_no_change_returns_empty(self):
        old = {'is_censored': False, 'is_removed': False, 'is_blocked': False}
        self.assertEqual(engine.diff_moderation_flags(old, old), [])

    def test_flag_turning_on_is_reported_as_set(self):
        old = {'is_censored': False, 'is_removed': False, 'is_blocked': False}
        new = {'is_censored': True, 'is_removed': False, 'is_blocked': False}
        changes = engine.diff_moderation_flags(old, new)
        self.assertEqual(changes, [engine.FlagChange('is_censored', engine.SET)])

    def test_flag_turning_off_is_reported_as_cleared(self):
        old = {'is_censored': True, 'is_removed': False, 'is_blocked': False}
        new = {'is_censored': False, 'is_removed': False, 'is_blocked': False}
        changes = engine.diff_moderation_flags(old, new)
        self.assertEqual(
            changes, [engine.FlagChange('is_censored', engine.CLEARED)])

    def test_multiple_flags_changing_at_once(self):
        old = {'is_censored': False, 'is_removed': False, 'is_blocked': False}
        new = {'is_censored': True, 'is_removed': True, 'is_blocked': False}
        changes = engine.diff_moderation_flags(old, new)
        self.assertEqual(
            {c.flag for c in changes}, {'is_censored', 'is_removed'})
        self.assertTrue(all(c.action == engine.SET for c in changes))

    def test_unrelated_keys_are_ignored(self):
        old = {'is_censored': False, 'is_removed': False, 'is_blocked': False,
              'comment': 'hello'}
        new = {'is_censored': False, 'is_removed': False, 'is_blocked': False,
              'comment': 'goodbye'}
        self.assertEqual(engine.diff_moderation_flags(old, new), [])

    def test_missing_keys_default_to_false(self):
        # A brand-new comment has no "old" state at all.
        old = {}
        new = {'is_censored': True}
        changes = engine.diff_moderation_flags(old, new)
        self.assertEqual(changes, [engine.FlagChange('is_censored', engine.SET)])


if __name__ == '__main__':
    unittest.main()
