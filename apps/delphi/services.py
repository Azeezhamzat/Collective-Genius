"""Bridges the real Question/Response models to the pure-Python Delphi
round-aggregation engine.
"""

from . import engine
from .models import Response


def responses_for_round(question, round_number):
    return Response.objects.filter(
        question=question, round_number=round_number)


def round_history(question):
    """engine.RoundStats for every round 1..question.current_round that
    has at least one response, in round order -- what
    ``engine.has_converged`` expects."""
    stats = []
    for round_number in range(1, question.current_round + 1):
        values = responses_for_round(question, round_number).values_list(
            'value', flat=True)
        stats.append(engine.aggregate_round(round_number, list(values)))
    return stats


def has_converged(question):
    return engine.has_converged(round_history(question))
