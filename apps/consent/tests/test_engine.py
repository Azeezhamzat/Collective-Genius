"""Unit tests for the pure-Python consent-decision engine.

No Django involved -- runs with a bare ``python -m unittest``.
"""

import unittest

from apps.consent import engine


def responses(rows):
    """rows: iterable of (participant_id, stance) or
    (participant_id, stance, resolved)."""
    out = []
    for row in rows:
        if len(row) == 2:
            pid, stance = row
            out.append(engine.Response(pid, stance))
        else:
            pid, stance, resolved = row
            out.append(engine.Response(pid, stance, resolved))
    return out


class ResolveTests(unittest.TestCase):

    def test_no_responses_means_no_consent(self):
        result = engine.resolve([])
        self.assertFalse(result.has_consent)

    def test_all_agree_has_consent(self):
        result = engine.resolve(responses([
            ('a', engine.AGREE), ('b', engine.AGREE),
        ]))
        self.assertTrue(result.has_consent)
        self.assertEqual(result.n_agree, 2)

    def test_agree_and_stand_aside_has_consent(self):
        # standing aside never blocks -- that's the point of the stance.
        result = engine.resolve(responses([
            ('a', engine.AGREE), ('b', engine.STAND_ASIDE),
        ]))
        self.assertTrue(result.has_consent)

    def test_single_unresolved_objection_blocks_consent_even_with_many_agrees(self):
        result = engine.resolve(responses([
            ('a', engine.AGREE), ('b', engine.AGREE),
            ('c', engine.AGREE), ('d', engine.AGREE),
            ('objector', engine.OBJECT),
        ]))
        self.assertFalse(result.has_consent)
        self.assertEqual(result.n_unresolved_objections, 1)
        self.assertEqual(result.unresolved_objector_ids, ['objector'])

    def test_resolved_objection_no_longer_blocks(self):
        result = engine.resolve(responses([
            ('a', engine.AGREE),
            ('objector', engine.OBJECT, True),  # resolved
        ]))
        self.assertTrue(result.has_consent)
        self.assertEqual(result.n_objections, 1)
        self.assertEqual(result.n_unresolved_objections, 0)

    def test_mix_of_resolved_and_unresolved_objections(self):
        result = engine.resolve(responses([
            ('resolved_objector', engine.OBJECT, True),
            ('active_objector', engine.OBJECT, False),
        ]))
        self.assertFalse(result.has_consent)
        self.assertEqual(result.n_objections, 2)
        self.assertEqual(result.n_unresolved_objections, 1)
        self.assertEqual(result.unresolved_objector_ids, ['active_objector'])

    def test_counts_are_accurate(self):
        result = engine.resolve(responses([
            ('a', engine.AGREE), ('b', engine.AGREE),
            ('c', engine.STAND_ASIDE),
            ('d', engine.OBJECT, True),
        ]))
        self.assertEqual(result.n_agree, 2)
        self.assertEqual(result.n_stand_aside, 1)
        self.assertEqual(result.n_objections, 1)


if __name__ == '__main__':
    unittest.main()
