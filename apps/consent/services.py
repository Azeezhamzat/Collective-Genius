"""Bridges the real Proposal/Response models to the pure-Python consent
engine.
"""

from . import engine
from .models import Response


def consent_for_proposal(proposal):
    """engine.ConsentResult for a proposal's current responses (one per
    participant -- Response has unique_together on (proposal, creator),
    so this is already deduplicated at the database level)."""
    rows = Response.objects.filter(proposal=proposal).values_list(
        'creator_id', 'stance', 'resolved')
    responses = [
        engine.Response(str(creator_id), stance, resolved)
        for creator_id, stance, resolved in rows
    ]
    return engine.resolve(responses)
