"""Pure-Python quadratic voting core.

Quadratic voting lets each participant spread a fixed budget of "voice
credits" across any number of options, where casting ``n`` votes on one
option costs ``n**2`` credits. Casting a strong preference for one option
therefore costs disproportionately more than spreading modest support
across several -- this surfaces the *intensity* of a group's preferences,
not just the direction of a majority, which a plain up/down vote cannot.

No Django dependency, so the budget and tallying rules are unit tested
standalone (see ``apps/quadraticvoting/tests/test_engine.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isqrt


def cost(votes: int) -> int:
    """Credits required to cast ``votes`` votes on one option.

    ``votes`` may be negative (voting against an option); cost is
    symmetric, since intensity of opposition should be no cheaper than
    intensity of support.
    """
    return votes * votes


def max_votes_for_budget(budget: int) -> int:
    """The most votes a participant could cast on a single option, given a
    total budget of ``budget`` credits and nothing spent elsewhere."""
    if budget < 0:
        raise ValueError('budget must be >= 0')
    return isqrt(budget)


@dataclass(frozen=True)
class Allocation:
    participant_id: str
    option_id: str
    votes: int  # positive = support, negative = oppose, 0 = no opinion


@dataclass
class BudgetError:
    participant_id: str
    spent: int
    budget: int


@dataclass
class OptionTally:
    option_id: str
    net_votes: int          # sum of votes, signed
    support_votes: int      # sum of positive votes
    oppose_votes: int       # sum of |negative votes|
    n_voters: int           # participants who cast a non-zero vote
    credits_spent: int      # sum of cost() across all voters on this option


def spent_by_participant(allocations):
    """{participant_id: total credits spent across all their allocations}"""
    spent = {}
    for a in allocations:
        spent[a.participant_id] = spent.get(a.participant_id, 0) + cost(a.votes)
    return spent


def validate_budgets(allocations, budget):
    """Return a list of BudgetError for every participant who has spent
    more than ``budget`` credits in total across ``allocations``. Empty
    list means every ballot is within budget.
    """
    errors = []
    for participant_id, spent in spent_by_participant(allocations).items():
        if spent > budget:
            errors.append(BudgetError(participant_id, spent, budget))
    return errors


def tally(allocations):
    """Aggregate every option's results across all participants.

    Does not itself enforce the budget -- callers that need a trustworthy
    result should reject or drop over-budget ballots (see
    ``validate_budgets``) before calling this, or pass only
    already-validated allocations.
    """
    by_option = {}
    for a in allocations:
        by_option.setdefault(a.option_id, []).append(a)

    results = []
    for option_id, votes in by_option.items():
        support = sum(v.votes for v in votes if v.votes > 0)
        oppose = sum(-v.votes for v in votes if v.votes < 0)
        results.append(OptionTally(
            option_id=option_id,
            net_votes=support - oppose,
            support_votes=support,
            oppose_votes=oppose,
            n_voters=sum(1 for v in votes if v.votes != 0),
            credits_spent=sum(cost(v.votes) for v in votes),
        ))

    results.sort(key=lambda r: r.net_votes, reverse=True)
    return results
