"""Pure-Python core for sociocracy/Loomio-style consent decisions.

Consent is a genuinely different decision rule from majority voting: a
proposal passes not because most people like it best, but because
*nobody has a standing objection to it*. Participants respond with one
of three stances:

* **agree** -- actively supports the proposal.
* **stand aside** -- doesn't support it, but won't block it (common for
  "not my area, but I won't stop the group").
* **object** -- blocks the proposal, and must give a reason. An
  objection can later be marked resolved (the proposer amended the
  proposal, or the objector was satisfied by discussion) without the
  objector having to change their stance.

A proposal has consent once there are no *unresolved* objections. This
deliberately doesn't count votes at all -- a proposal with one
unresolved objection and fifty agreements still has no consent, by
design: consent protects against steamrolling a real, unaddressed
concern.

No Django dependency, so this is unit tested standalone.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

AGREE = 'agree'
STAND_ASIDE = 'stand_aside'
OBJECT = 'object'

STANCES = (AGREE, STAND_ASIDE, OBJECT)


@dataclass(frozen=True)
class Response:
    participant_id: str
    stance: str
    resolved: bool = False  # only meaningful when stance == OBJECT


@dataclass
class ConsentResult:
    has_consent: bool
    n_agree: int
    n_stand_aside: int
    n_objections: int
    n_unresolved_objections: int
    unresolved_objector_ids: list = field(default_factory=list)


def resolve(responses):
    """Determine whether a proposal currently has consent.

    ``responses``: iterable of Response, one **current** response per
    participant (if a participant changed their stance, only their
    latest response should be passed in -- this function doesn't dedupe
    by participant, callers own that).

    A proposal with zero responses has not been consented to -- silence
    isn't agreement.
    """
    responses = list(responses)
    agree = [r for r in responses if r.stance == AGREE]
    stand_aside = [r for r in responses if r.stance == STAND_ASIDE]
    objections = [r for r in responses if r.stance == OBJECT]
    unresolved = [r for r in objections if not r.resolved]

    return ConsentResult(
        has_consent=bool(responses) and not unresolved,
        n_agree=len(agree),
        n_stand_aside=len(stand_aside),
        n_objections=len(objections),
        n_unresolved_objections=len(unresolved),
        unresolved_objector_ids=[r.participant_id for r in unresolved],
    )
