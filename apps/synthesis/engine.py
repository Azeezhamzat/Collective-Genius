"""Pure-Python opinion clustering and consensus-detection engine.

This module has no Django or third-party ML dependency on purpose: it keeps
the actual algorithm trivial to unit test in isolation, and easy to swap out
later for a heavier implementation (numpy/scikit-learn, or an LLM-assisted
clusterer) without touching the Django integration layer in ``services.py``.

The approach is a simplified, from-scratch take on the "bridging statement"
idea popularized by Polis/pol.is: split participants into opinion groups
based on their agree/disagree pattern across statements, then report, for
every statement, whether it builds consensus across groups ("bridging"),
splits the groups apart ("divisive"), or is simply not engaged with enough
to say. This is deliberately not a re-implementation of Polis' actual
PCA + k-means pipeline -- it is a much simpler two-group heuristic that is
easy to reason about and verify, meant as a first, honest version of the
feature rather than a claim of parity.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

AGREE = 1
DISAGREE = -1


@dataclass(frozen=True)
class Vote:
    participant_id: str
    statement_id: str
    value: int  # AGREE or DISAGREE


@dataclass
class StatementStats:
    statement_id: str
    n_votes: int
    agree_ratio: float  # overall agreement, across all participants
    group_agree_ratio: dict  # {group_id: agree_ratio within that group}
    consensus_score: float  # min agree_ratio across groups (high = consensus)
    divisiveness: float  # max gap between any two groups' agree_ratio


@dataclass
class ClusteringResult:
    groups: dict  # {participant_id: group_id}
    group_sizes: dict  # {group_id: count}
    statements: list  # list[StatementStats], sorted by consensus_score desc
    n_groups: int


def _vote_matrix(votes):
    """Build participant_id -> {statement_id: value}."""
    matrix = {}
    for v in votes:
        matrix.setdefault(v.participant_id, {})[v.statement_id] = v.value
    return matrix


def cluster_participants(votes, n_groups=2, max_iterations=25,
                          seed_statement_id=None):
    """Split participants into ``n_groups`` opinion groups.

    Runs a k-means-style loop over each participant's vote vector: seed the
    groups from the most divisive statement available (or the caller
    supplied ``seed_statement_id``), then repeatedly reassign each
    participant to whichever group's average vote vector they agree with
    most, recomputing group centroids each round, until assignments stop
    changing or ``max_iterations`` is reached.

    Only ``n_groups=2`` is supported today -- that already answers the two
    questions that matter most for a discussion: where does this group
    actually agree, and where does it split. Returns an empty/degenerate
    assignment when there isn't enough data to say anything meaningful.
    """
    if n_groups != 2:
        raise NotImplementedError(
            'cluster_participants currently only supports n_groups=2')

    matrix = _vote_matrix(votes)
    participant_ids = list(matrix.keys())
    statement_ids = sorted({v.statement_id for v in votes})

    if len(participant_ids) < 2 or not statement_ids:
        return {pid: 0 for pid in participant_ids}

    if seed_statement_id is None:
        seed_statement_id = _most_divisive_statement(matrix, statement_ids)

    groups = {
        pid: (0 if matrix[pid].get(seed_statement_id) != DISAGREE else 1)
        for pid in participant_ids
    }

    for _ in range(max_iterations):
        centroids = _group_centroids(matrix, groups, statement_ids, n_groups)
        changed = False
        for pid in participant_ids:
            best_group, best_score = groups[pid], None
            for gid, centroid in centroids.items():
                score = _agreement_with_centroid(matrix[pid], centroid)
                if score is not None and (
                        best_score is None or score > best_score):
                    best_group, best_score = gid, score
            if best_group != groups[pid]:
                groups[pid] = best_group
                changed = True
        if not changed:
            break

    return groups


def _most_divisive_statement(matrix, statement_ids):
    best_id, best_spread = statement_ids[0], -1
    for sid in statement_ids:
        values = [votes[sid] for votes in matrix.values() if sid in votes]
        if not values:
            continue
        agree = sum(1 for v in values if v == AGREE)
        disagree = len(values) - agree
        spread = min(agree, disagree)
        if spread > best_spread:
            best_id, best_spread = sid, spread
    return best_id


def _group_centroids(matrix, groups, statement_ids, n_groups):
    sums = {g: {sid: 0.0 for sid in statement_ids} for g in range(n_groups)}
    counts = {g: {sid: 0 for sid in statement_ids} for g in range(n_groups)}
    for pid, votes in matrix.items():
        g = groups[pid]
        for sid, value in votes.items():
            sums[g][sid] += value
            counts[g][sid] += 1
    return {
        g: {
            sid: (sums[g][sid] / counts[g][sid]) if counts[g][sid] else 0.0
            for sid in statement_ids
        }
        for g in range(n_groups)
    }


def _agreement_with_centroid(participant_votes, centroid):
    shared = [(v, centroid[sid]) for sid, v in participant_votes.items()
              if sid in centroid]
    if not shared:
        return None
    return mean(v * c for v, c in shared)


def analyze(votes, n_groups=2, min_votes_per_statement=1):
    """Run the full pipeline: cluster participants, then score every
    statement for consensus (agreed across groups) and divisiveness (split
    between groups).
    """
    groups = cluster_participants(votes, n_groups=n_groups)
    group_sizes = {}
    for g in groups.values():
        group_sizes[g] = group_sizes.get(g, 0) + 1

    by_statement = {}
    for v in votes:
        by_statement.setdefault(v.statement_id, []).append(v)

    statements = []
    for sid, statement_votes in by_statement.items():
        if len(statement_votes) < min_votes_per_statement:
            continue
        agree = sum(1 for v in statement_votes if v.value == AGREE)
        agree_ratio = agree / len(statement_votes)

        group_agree = {}
        for g in set(groups.values()):
            g_votes = [v for v in statement_votes
                       if groups.get(v.participant_id) == g]
            if g_votes:
                g_agree = sum(1 for v in g_votes if v.value == AGREE)
                group_agree[g] = g_agree / len(g_votes)

        if group_agree:
            consensus_score = min(group_agree.values())
            divisiveness = max(group_agree.values()) - min(
                group_agree.values())
        else:
            consensus_score = agree_ratio
            divisiveness = 0.0

        statements.append(StatementStats(
            statement_id=sid,
            n_votes=len(statement_votes),
            agree_ratio=agree_ratio,
            group_agree_ratio=group_agree,
            consensus_score=consensus_score,
            divisiveness=divisiveness,
        ))

    statements.sort(key=lambda s: s.consensus_score, reverse=True)

    return ClusteringResult(
        groups=groups,
        group_sizes=group_sizes,
        statements=statements,
        n_groups=len(group_sizes) or n_groups,
    )
