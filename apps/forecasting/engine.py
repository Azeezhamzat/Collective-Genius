"""Pure-Python core for prediction-market-style forecasting.

Participants forecast the probability of a yes/no outcome (0..1) for a
question with a clear, checkable resolution criterion. Once resolved,
two things become interesting:

1. The **aggregate forecast** -- the crowd's collective estimate,
  typically just the mean of everyone's individual probability. This is
  "wisdom of crowds" applied to prediction rather than voting: a group
  forecast is frequently better calibrated than any single expert's.
2. Each forecaster's **Brier score** -- the standard, simple proper
  scoring rule for probabilistic forecasts (Brier, 1950):
  ``(probability - outcome) ** 2``, lower is better, 0 is a perfect
  forecast. Track it over many resolved questions and you get a
  genuine, auditable measure of forecasting skill -- not just "who
  guessed right this once" but "who is reliably well-calibrated."

No Django dependency, so all of this is unit tested standalone.
"""

from __future__ import annotations

from dataclasses import dataclass


def brier_score(probability, outcome):
    """The Brier score for one forecast.

    ``probability``: the forecaster's stated probability of the "yes"
    outcome, in [0, 1].
    ``outcome``: 1 if "yes" happened, 0 if "no" happened.
    Returns a value in [0, 1] -- 0 is a perfect forecast, 1 is
    maximally wrong (confidently predicted the outcome that didn't
    happen).
    """
    return (probability - outcome) ** 2


def aggregate_forecast(probabilities):
    """The crowd's aggregate forecast: the mean of everyone's stated
    probability. Returns None if ``probabilities`` is empty.
    """
    probabilities = list(probabilities)
    if not probabilities:
        return None
    return sum(probabilities) / len(probabilities)


@dataclass
class ForecasterScore:
    forecaster_id: str
    mean_brier_score: float
    n_questions: int


def leaderboard(scored_forecasts):
    """Rank forecasters by mean Brier score across every *resolved*
    question they forecast, best (lowest) first.

    ``scored_forecasts``: iterable of (forecaster_id, probability,
    outcome) -- one row per forecaster per resolved question. Forecasts
    on unresolved questions have no outcome yet and must not be passed
    in (there is nothing to score them against).
    """
    by_forecaster = {}
    for forecaster_id, probability, outcome in scored_forecasts:
        by_forecaster.setdefault(forecaster_id, []).append(
            brier_score(probability, outcome))

    results = [
        ForecasterScore(
            forecaster_id=forecaster_id,
            mean_brier_score=sum(scores) / len(scores),
            n_questions=len(scores),
        )
        for forecaster_id, scores in by_forecaster.items()
    ]
    results.sort(key=lambda r: r.mean_brier_score)
    return results
