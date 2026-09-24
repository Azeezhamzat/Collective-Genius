"""Unit tests for the pure-Python quadratic voting engine.

No Django involved -- runs with a bare ``python -m unittest``.
"""

import unittest

from apps.quadraticvoting import engine


def allocations(rows):
    """rows: iterable of (participant_id, option_id, votes)."""
    return [engine.Allocation(p, o, v) for p, o, v in rows]


class CostTests(unittest.TestCase):

    def test_cost_is_quadratic(self):
        self.assertEqual(engine.cost(0), 0)
        self.assertEqual(engine.cost(1), 1)
        self.assertEqual(engine.cost(3), 9)
        self.assertEqual(engine.cost(10), 100)

    def test_cost_symmetric_for_negative_votes(self):
        self.assertEqual(engine.cost(-4), engine.cost(4))

    def test_max_votes_for_budget(self):
        self.assertEqual(engine.max_votes_for_budget(0), 0)
        self.assertEqual(engine.max_votes_for_budget(1), 1)
        self.assertEqual(engine.max_votes_for_budget(99), 9)   # 9**2 = 81
        self.assertEqual(engine.max_votes_for_budget(100), 10)  # 10**2 = 100

    def test_max_votes_rejects_negative_budget(self):
        with self.assertRaises(ValueError):
            engine.max_votes_for_budget(-1)


class ValidateBudgetsTests(unittest.TestCase):

    def test_empty_allocations_have_no_errors(self):
        self.assertEqual(engine.validate_budgets([], budget=100), [])

    def test_within_budget_has_no_errors(self):
        # 3 votes on A (cost 9) + 4 votes on B (cost 16) = 25 <= 100
        rows = allocations([('p1', 'A', 3), ('p1', 'B', 4)])
        self.assertEqual(engine.validate_budgets(rows, budget=100), [])

    def test_over_budget_is_reported(self):
        # 10 votes (cost 100) + 5 votes (cost 25) = 125 > 100
        rows = allocations([('p1', 'A', 10), ('p1', 'B', 5)])
        errors = engine.validate_budgets(rows, budget=100)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].participant_id, 'p1')
        self.assertEqual(errors[0].spent, 125)
        self.assertEqual(errors[0].budget, 100)

    def test_only_over_budget_participants_are_reported(self):
        rows = allocations([
            ('p1', 'A', 10),   # cost 100, exactly at budget: fine
            ('p2', 'A', 11),   # cost 121: over budget
        ])
        errors = engine.validate_budgets(rows, budget=100)
        self.assertEqual([e.participant_id for e in errors], ['p2'])

    def test_negative_votes_count_toward_budget_too(self):
        rows = allocations([('p1', 'A', -10), ('p1', 'B', -5)])
        errors = engine.validate_budgets(rows, budget=100)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].spent, 125)


class TallyTests(unittest.TestCase):

    def test_empty_allocations_tally_to_nothing(self):
        self.assertEqual(engine.tally([]), [])

    def test_single_option_aggregates_across_participants(self):
        rows = allocations([
            ('p1', 'A', 5),
            ('p2', 'A', 3),
            ('p3', 'A', -2),
        ])
        results = engine.tally(rows)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result.option_id, 'A')
        self.assertEqual(result.support_votes, 8)
        self.assertEqual(result.oppose_votes, 2)
        self.assertEqual(result.net_votes, 6)
        self.assertEqual(result.n_voters, 3)
        self.assertEqual(result.credits_spent, 25 + 9 + 4)

    def test_results_sorted_by_net_votes_descending(self):
        rows = allocations([
            ('p1', 'popular', 10),
            ('p1', 'unpopular', -10),
            ('p1', 'middling', 1),
        ])
        results = engine.tally(rows)
        self.assertEqual(
            [r.option_id for r in results],
            ['popular', 'middling', 'unpopular'])

    def test_zero_votes_do_not_count_as_a_voter(self):
        rows = allocations([('p1', 'A', 0), ('p2', 'A', 3)])
        results = engine.tally(rows)
        self.assertEqual(results[0].n_voters, 1)


if __name__ == '__main__':
    unittest.main()
