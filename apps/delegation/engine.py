"""Pure-Python core for liquid democracy: instead of only voting
directly or only delegating to a party list, a participant can either
cast a direct vote or delegate it to someone they trust -- who may
themselves have delegated onward, forming a chain that ends wherever
someone actually votes.

This is a genuinely different decision mechanism from everything else
in this rebuild (quadratic voting, consent, Delphi, forecasting are all
"everyone decides for themselves" mechanisms); it's included because
letting trust substitute for direct engagement, transitively, is one of
the best-known tools for a large group to reach a considered collective
decision without requiring everyone to have researched every question
themselves.
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_CHAIN_DEPTH = 50


@dataclass(frozen=True)
class Ballot:
    voter_id: str
    option_id: str


@dataclass(frozen=True)
class Delegation:
    delegator_id: str
    delegatee_id: str


@dataclass(frozen=True)
class OptionTally:
    option_id: str
    votes: int


def _delegation_map(delegations):
    return {d.delegator_id: d.delegatee_id for d in delegations}


def resolve_final_voter(voter_id, delegation_map, max_depth=MAX_CHAIN_DEPTH):
    """Follow ``voter_id``'s outgoing delegation chain to whoever will
    actually decide -- the first person in the chain with no outgoing
    delegation of their own.

    Returns ``None`` (not that person's id) if the chain loops back on
    itself, or runs past ``max_depth`` without terminating (an
    unreasonably long chain is, practically, as broken as a cycle). In
    either case the delegation is void: nobody in this chain has
    actually decided for ``voter_id``, so a caller should treat this as
    "abstained", never as "voted for whoever happened to be last
    followed".
    """
    seen = {voter_id}
    current = voter_id
    for _ in range(max_depth):
        next_id = delegation_map.get(current)
        if next_id is None:
            return current
        if next_id in seen:
            return None
        seen.add(next_id)
        current = next_id
    return None


def tally(direct_votes, delegations):
    """Count votes for every option, resolving delegated votes through
    their chains.

    ``direct_votes``: list[Ballot] -- people who voted for themselves.
    ``delegations``: list[Delegation] -- people who delegated instead.

    A delegator who *also* appears in ``direct_votes`` is treated as
    having voted directly -- their own ballot always takes precedence
    over a delegation on file, so nobody can be out-voted by their own
    stale delegation. A chain that cycles, runs too long, or dead-ends
    on someone who never cast a direct vote contributes nothing to any
    option -- that's a real abstention, not a bug to paper over.

    Returns a list of ``OptionTally``, most votes first (ties broken by
    ``option_id`` for a stable, deterministic order).
    """
    direct_by_voter = {b.voter_id: b.option_id for b in direct_votes}
    delegation_map = _delegation_map(delegations)

    counts = {}
    for option_id in direct_by_voter.values():
        counts[option_id] = counts.get(option_id, 0) + 1

    for delegator_id in delegation_map:
        if delegator_id in direct_by_voter:
            continue
        final_voter = resolve_final_voter(delegator_id, delegation_map)
        if final_voter is None or final_voter not in direct_by_voter:
            continue
        option_id = direct_by_voter[final_voter]
        counts[option_id] = counts.get(option_id, 0) + 1

    return sorted(
        (OptionTally(option_id, votes)
         for option_id, votes in counts.items()),
        key=lambda t: (-t.votes, t.option_id),
    )


def voting_power(direct_votes, delegations):
    """``{voter_id: power}`` for every person who voted directly --
    their own vote plus everyone whose delegation chain currently
    resolves to them. Surfacing this (e.g. "12 people's votes are
    currently routed through you") is a standard liquid-democracy
    transparency expectation, not an optional extra: delegating your
    vote to someone should come with visibility into how much say
    they've accumulated.
    """
    direct_by_voter = {b.voter_id: b.option_id for b in direct_votes}
    delegation_map = _delegation_map(delegations)
    power = {voter_id: 1 for voter_id in direct_by_voter}

    for delegator_id in delegation_map:
        if delegator_id in direct_by_voter:
            continue
        final_voter = resolve_final_voter(delegator_id, delegation_map)
        if final_voter is not None and final_voter in power:
            power[final_voter] += 1

    return power
