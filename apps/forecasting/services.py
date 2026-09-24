"""Bridges the real Question/Forecast models to the pure-Python
forecasting engine.
"""

from . import engine
from .models import Forecast
from .models import Question


def forecast_for_participant(question, user):
    return Forecast.objects.filter(question=question, creator=user).first()


def aggregate_for_question(question):
    """The crowd's aggregate forecast for one question, as a 0..1
    probability, or None if nobody has forecast yet."""
    probabilities = Forecast.objects.filter(
        question=question).values_list('probability', flat=True)
    return engine.aggregate_forecast([p / 100 for p in probabilities])


def leaderboard_for_module(module):
    """engine.ForecasterScore list across every resolved question in
    ``module``, best-calibrated first."""
    resolved_questions = Question.objects.filter(
        module=module, is_resolved=True, outcome__isnull=False)
    rows = (
        Forecast.objects
        .filter(question__in=resolved_questions)
        .select_related('question')
        .values_list('creator_id', 'probability', 'question__outcome')
    )
    scored_forecasts = [
        (str(creator_id), probability / 100, int(outcome))
        for creator_id, probability, outcome in rows
    ]
    return engine.leaderboard(scored_forecasts)
