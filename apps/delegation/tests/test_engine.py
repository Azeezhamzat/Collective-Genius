import unittest

from apps.delegation import engine


class ResolveFinalVoterTests(unittest.TestCase):

    def test_no_delegation_resolves_to_self(self):
        self.assertEqual(engine.resolve_final_voter('a', {}), 'a')

    def test_single_hop_resolves_to_delegatee(self):
        self.assertEqual(
            engine.resolve_final_voter('a', {'a': 'b'}), 'b')

    def test_transitive_chain_resolves_to_final_link(self):
        chain = {'a': 'b', 'b': 'c', 'c': 'd'}
        self.assertEqual(engine.resolve_final_voter('a', chain), 'd')

    def test_direct_cycle_returns_none(self):
        chain = {'a': 'b', 'b': 'a'}
        self.assertIsNone(engine.resolve_final_voter('a', chain))

    def test_self_delegation_returns_none(self):
        self.assertIsNone(engine.resolve_final_voter('a', {'a': 'a'}))

    def test_longer_cycle_returns_none(self):
        chain = {'a': 'b', 'b': 'c', 'c': 'a'}
        self.assertIsNone(engine.resolve_final_voter('a', chain))

    def test_chain_exceeding_max_depth_returns_none(self):
        chain = {str(i): str(i + 1) for i in range(100)}
        self.assertIsNone(
            engine.resolve_final_voter('0', chain, max_depth=10))


class TallyTests(unittest.TestCase):

    def test_direct_votes_are_counted(self):
        votes = [engine.Ballot('a', 'yes'), engine.Ballot('b', 'no')]
        result = engine.tally(votes, [])
        self.assertEqual(
            {t.option_id: t.votes for t in result}, {'yes': 1, 'no': 1})

    def test_delegated_vote_counts_for_delegatee_choice(self):
        votes = [engine.Ballot('b', 'yes')]
        delegations = [engine.Delegation('a', 'b')]
        result = engine.tally(votes, delegations)
        self.assertEqual(
            {t.option_id: t.votes for t in result}, {'yes': 2})

    def test_transitive_delegation_counts_for_final_voters_choice(self):
        votes = [engine.Ballot('c', 'no')]
        delegations = [
            engine.Delegation('a', 'b'), engine.Delegation('b', 'c')]
        result = engine.tally(votes, delegations)
        self.assertEqual(
            {t.option_id: t.votes for t in result}, {'no': 3})

    def test_own_ballot_overrides_a_stale_delegation(self):
        votes = [engine.Ballot('a', 'yes'), engine.Ballot('b', 'no')]
        delegations = [engine.Delegation('a', 'b')]
        result = engine.tally(votes, delegations)
        # a voted directly for 'yes', so a's delegation to b is ignored.
        self.assertEqual(
            {t.option_id: t.votes for t in result}, {'yes': 1, 'no': 1})

    def test_cycle_abstains(self):
        votes = [engine.Ballot('c', 'yes')]
        delegations = [
            engine.Delegation('a', 'b'), engine.Delegation('b', 'a')]
        result = engine.tally(votes, delegations)
        self.assertEqual(
            {t.option_id: t.votes for t in result}, {'yes': 1})

    def test_dead_end_delegation_abstains(self):
        votes = []
        delegations = [engine.Delegation('a', 'b')]
        result = engine.tally(votes, delegations)
        self.assertEqual(result, [])

    def test_results_sorted_by_votes_descending(self):
        votes = [
            engine.Ballot('a', 'yes'),
            engine.Ballot('b', 'yes'),
            engine.Ballot('c', 'no'),
        ]
        result = engine.tally(votes, [])
        self.assertEqual([t.option_id for t in result], ['yes', 'no'])

    def test_ties_broken_by_option_id_for_stable_order(self):
        votes = [engine.Ballot('a', 'b_option'), engine.Ballot('c', 'a_option')]
        result = engine.tally(votes, [])
        self.assertEqual([t.option_id for t in result], ['a_option', 'b_option'])


class VotingPowerTests(unittest.TestCase):

    def test_direct_voter_with_no_delegators_has_power_one(self):
        votes = [engine.Ballot('a', 'yes')]
        power = engine.voting_power(votes, [])
        self.assertEqual(power, {'a': 1})

    def test_direct_delegator_adds_to_delegatees_power(self):
        votes = [engine.Ballot('b', 'yes')]
        delegations = [engine.Delegation('a', 'b')]
        power = engine.voting_power(votes, delegations)
        self.assertEqual(power, {'b': 2})

    def test_transitive_delegators_all_add_to_final_voters_power(self):
        votes = [engine.Ballot('c', 'yes')]
        delegations = [
            engine.Delegation('a', 'b'), engine.Delegation('b', 'c')]
        power = engine.voting_power(votes, delegations)
        self.assertEqual(power, {'c': 3})

    def test_delegation_to_someone_who_never_votes_grants_no_power(self):
        power = engine.voting_power([], [engine.Delegation('a', 'b')])
        self.assertEqual(power, {})

    def test_own_ballot_keeps_own_power_despite_stale_delegation(self):
        votes = [engine.Ballot('a', 'yes'), engine.Ballot('b', 'no')]
        delegations = [engine.Delegation('a', 'b')]
        power = engine.voting_power(votes, delegations)
        self.assertEqual(power, {'a': 1, 'b': 1})


if __name__ == '__main__':
    unittest.main()
