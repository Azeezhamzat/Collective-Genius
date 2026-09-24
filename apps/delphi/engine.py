"""Pure-Python round aggregation and convergence measurement for
Delphi-method structured elicitation.

The Delphi method: a group of participants each give a numeric estimate
for a question, anonymously (nobody sees who said what, only the
aggregate). The aggregate -- typically the median and spread -- is
shown back to everyone, and a new round opens where participants can
revise their estimate in light of the group's response. Repeated over a
few rounds, estimates typically converge without anyone having to
defend a position socially (the anonymity is the point: it avoids
groupthink and status-based anchoring that a face-to-face discussion or
even a named-discussion platform can't fully avoid).

This module has no Django dependency, so both the per-round aggregation
and the convergence check are unit tested standalone.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass
class RoundStats:
    round_number: int
    n_responses: int
    median: float
    mean: float
    stdev: float
    minimum: float
    maximum: float


def aggregate_round(round_number, values):
    """Summary statistics for one round's responses. Returns None if
    ``values`` is empty. ``stdev`` is the population standard deviation
    (0.0 for a single response -- there's nothing to spread)."""
    values = list(values)
    if not values:
        return None
    return RoundStats(
        round_number=round_number,
        n_responses=len(values),
        median=statistics.median(values),
        mean=statistics.mean(values),
        stdev=statistics.pstdev(values) if len(values) > 1 else 0.0,
        minimum=min(values),
        maximum=max(values),
    )


def has_converged(round_stats_sequence, threshold_ratio=0.5):
    """Has the group's spread of estimates tightened meaningfully since
    the first round?

    True if the latest round's standard deviation is at most
    ``threshold_ratio`` times the first round's -- a simple, transparent
    signal (default: spread has at least halved). False if there are
    fewer than two rounds to compare, or if the first round already had
    zero spread (there's nothing to converge from -- everyone already
    agreed on round one, which isn't the same as the group converging
    through the process).

    ``round_stats_sequence``: RoundStats in round order; a None entry
    (an empty round) is skipped.
    """
    rounds = [r for r in round_stats_sequence if r is not None]
    if len(rounds) < 2:
        return False

    first, latest = rounds[0], rounds[-1]
    if first.stdev == 0:
        return False

    return latest.stdev <= first.stdev * threshold_ratio
