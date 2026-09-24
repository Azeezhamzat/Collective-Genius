"""Unit tests for the pure-Python synthesis engine.

These deliberately avoid Django entirely (no DB, no settings) so they can
run with a bare ``python -m unittest`` -- useful in this codebase where the
full test suite needs the whole (old, heavy) dependency stack installed.
"""

import unittest

from apps.synthesis import engine


def votes(rows):
    """rows: iterable of (participant_id, statement_id, value)."""
    return [engine.Vote(p, s, v) for p, s, v in rows]


class ClusterParticipantsTests(unittest.TestCase):

    def test_no_participants_returns_empty(self):
        self.assertEqual(engine.cluster_participants([]), {})

    def test_single_participant_returns_single_group(self):
        result = engine.cluster_participants(
            votes([('p1', 's1', engine.AGREE)]))
        self.assertEqual(result, {'p1': 0})

    def test_splits_two_clear_camps(self):
        # Camp A always agrees with camp A and disagrees with camp B's
        # distinctive statements; camp B is the mirror image.
        rows = []
        camp_a = ['a1', 'a2', 'a3']
        camp_b = ['b1', 'b2', 'b3']
        for p in camp_a:
            rows += [
                (p, 's_bridge', engine.AGREE),
                (p, 's_a', engine.AGREE),
                (p, 's_b', engine.DISAGREE),
            ]
        for p in camp_b:
            rows += [
                (p, 's_bridge', engine.AGREE),
                (p, 's_a', engine.DISAGREE),
                (p, 's_b', engine.AGREE),
            ]

        groups = engine.cluster_participants(votes(rows))

        # Every member of a camp must land in the same group as their
        # camp-mates, and the two camps must land in different groups
        # (group *labels* are arbitrary, so compare relative membership).
        a_groups = {groups[p] for p in camp_a}
        b_groups = {groups[p] for p in camp_b}
        self.assertEqual(len(a_groups), 1, 'camp A split across groups')
        self.assertEqual(len(b_groups), 1, 'camp B split across groups')
        self.assertNotEqual(a_groups, b_groups,
                            'the two camps were merged into one group')


class AnalyzeTests(unittest.TestCase):

    def setUp(self):
        camp_a = ['a1', 'a2', 'a3']
        camp_b = ['b1', 'b2', 'b3']
        rows = []
        for p in camp_a:
            rows += [
                (p, 's_bridge', engine.AGREE),
                (p, 's_a_only', engine.AGREE),
                (p, 's_b_only', engine.DISAGREE),
            ]
        for p in camp_b:
            rows += [
                (p, 's_bridge', engine.AGREE),
                (p, 's_a_only', engine.DISAGREE),
                (p, 's_b_only', engine.AGREE),
            ]
        self.result = engine.analyze(votes(rows))
        self.by_id = {s.statement_id: s for s in self.result.statements}

    def test_two_groups_detected(self):
        self.assertEqual(self.result.n_groups, 2)
        self.assertEqual(sum(self.result.group_sizes.values()), 6)

    def test_bridge_statement_has_highest_consensus(self):
        top = self.result.statements[0]
        self.assertEqual(top.statement_id, 's_bridge')
        self.assertAlmostEqual(top.consensus_score, 1.0)
        self.assertAlmostEqual(top.divisiveness, 0.0)

    def test_camp_only_statements_are_divisive(self):
        for sid in ('s_a_only', 's_b_only'):
            stat = self.by_id[sid]
            self.assertAlmostEqual(stat.divisiveness, 1.0, msg=sid)
            self.assertAlmostEqual(stat.consensus_score, 0.0, msg=sid)

    def test_statements_below_min_votes_are_excluded(self):
        rows = [('p1', 's1', engine.AGREE), ('p1', 's2', engine.AGREE),
                ('p2', 's2', engine.DISAGREE)]
        result = engine.analyze(votes(rows), min_votes_per_statement=2)
        ids = {s.statement_id for s in result.statements}
        self.assertNotIn('s1', ids)
        self.assertIn('s2', ids)


if __name__ == '__main__':
    unittest.main()
