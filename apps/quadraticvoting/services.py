"""Bridges the quadratic-voting models to the pure-Python engine, and
handles saving a participant's ballot transactionally.
"""

from django.db import transaction

from . import engine
from .models import Allocation


def allocations_for_round(voting_round):
    return Allocation.objects.filter(option__voting_round=voting_round)


def ballot_for_participant(voting_round, user):
    """{option_id: votes} for everything this user has already allocated
    in this round."""
    qs = allocations_for_round(voting_round).filter(creator=user)
    return {a.option_id: a.votes for a in qs}


class BallotRejected(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__('Ballot exceeds budget: {}'.format(errors))


@transaction.atomic
def save_ballot(voting_round, user, votes_by_option_id):
    """Validate and persist one participant's full ballot for a round.

    ``votes_by_option_id``: {option_id: votes}, covering every option the
    participant wants a non-zero allocation on (options left out are
    treated as 0 and any existing allocation for them is cleared).

    Raises ``BallotRejected`` (and saves nothing) if the ballot would put
    this participant over the round's credit budget.
    """
    engine_allocations = [
        engine.Allocation(str(user.pk), str(option_id), votes)
        for option_id, votes in votes_by_option_id.items()
    ]
    errors = engine.validate_budgets(
        engine_allocations, budget=voting_round.credit_budget)
    if errors:
        raise BallotRejected(errors)

    option_ids = set(votes_by_option_id) | set(
        allocations_for_round(voting_round)
        .filter(creator=user)
        .values_list('option_id', flat=True)
    )
    for option_id in option_ids:
        votes = votes_by_option_id.get(option_id, 0)
        if votes == 0:
            Allocation.objects.filter(
                option_id=option_id, creator=user).delete()
        else:
            Allocation.objects.update_or_create(
                option_id=option_id, creator=user,
                defaults={'votes': votes},
            )


def tally_round(voting_round):
    """engine.OptionTally list for every option in ``voting_round``,
    keyed back to real Option rows by the caller (results are returned
    with ``option_id`` as a string, matching ``str(Option.pk)``).
    """
    allocations = [
        engine.Allocation(str(a.creator_id), str(a.option_id), a.votes)
        for a in allocations_for_round(voting_round)
    ]
    return engine.tally(allocations)
