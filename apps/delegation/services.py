"""Bridges DelegationRound/Option/Vote/Delegation to the pure-Python
liquid-democracy engine, and handles casting a vote or a delegation
transactionally -- the two are mutually exclusive per participant per
round, enforced here rather than left to the caller.
"""

from django.db import transaction

from . import engine
from .models import Delegation
from .models import Vote


def votes_for_round(delegation_round):
    return Vote.objects.filter(delegation_round=delegation_round)


def delegations_for_round(delegation_round):
    return Delegation.objects.filter(delegation_round=delegation_round)


def my_choice(delegation_round, user):
    """What ``user`` has done in this round so far: ``('voted',
    option)``, ``('delegated', delegatee_user)``, or ``(None, None)``
    if they've done neither yet.
    """
    vote = votes_for_round(delegation_round).filter(creator=user).first()
    if vote is not None:
        return 'voted', vote.option
    delegation = delegations_for_round(delegation_round) \
        .filter(delegator=user).first()
    if delegation is not None:
        return 'delegated', delegation.delegatee
    return None, None


@transaction.atomic
def cast_vote(delegation_round, user, option):
    """Record a direct vote, removing any standing delegation for this
    round -- voting always supersedes delegating, never coexists with
    it (see the Vote model docstring)."""
    Delegation.objects.filter(
        delegation_round=delegation_round, delegator=user).delete()
    Vote.objects.update_or_create(
        delegation_round=delegation_round, creator=user,
        defaults={'option': option},
    )


@transaction.atomic
def cast_delegation(delegation_round, user, delegatee):
    """Record a delegation, removing any direct vote this round --
    same mutual-exclusion reasoning as ``cast_vote``."""
    Vote.objects.filter(
        delegation_round=delegation_round, creator=user).delete()
    Delegation.objects.update_or_create(
        delegation_round=delegation_round, delegator=user,
        defaults={'delegatee': delegatee},
    )


def revoke(delegation_round, user):
    """Remove whatever ``user`` has on file for this round (vote or
    delegation), leaving them undecided again."""
    Vote.objects.filter(
        delegation_round=delegation_round, creator=user).delete()
    Delegation.objects.filter(
        delegation_round=delegation_round, delegator=user).delete()


def _engine_inputs(delegation_round):
    votes = [
        engine.Ballot(str(v.creator_id), str(v.option_id))
        for v in votes_for_round(delegation_round)
    ]
    delegations = [
        engine.Delegation(str(d.delegator_id), str(d.delegatee_id))
        for d in delegations_for_round(delegation_round)
    ]
    return votes, delegations


def tally_round(delegation_round):
    """engine.OptionTally list for every option with at least one
    (direct or resolved-delegated) vote, keyed back to real Option rows
    by the caller (results carry ``option_id`` as a string, matching
    ``str(Option.pk)``)."""
    votes, delegations = _engine_inputs(delegation_round)
    return engine.tally(votes, delegations)


def voting_power_for_round(delegation_round):
    """{creator_id (int): power} for every participant who voted
    directly in this round -- see engine.voting_power. Keys are
    returned as ints (matching Vote.creator_id) for easy lookup against
    real User rows."""
    votes, delegations = _engine_inputs(delegation_round)
    power = engine.voting_power(votes, delegations)
    return {int(voter_id): count for voter_id, count in power.items()}
