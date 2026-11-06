from .ComparisonRule import ComparisonRule
from ..CurrentAttempt import CurrentAttempt
from ..PreviousAttempts import PreviousAttempts

class RiskScoreComparison(ComparisonRule):
    """Compare either mental wellness risk or burnout risk."""

    def __init__(self, field: str, label: str):
        self._field = field
        self._label = label

    def evaluate(
        self,
        current: CurrentAttempt,
        history: PreviousAttempts,
    ) -> str | None:
        previous = history.get_latest(self._field)

        if previous is None:
            return None

        risk_score = getattr(current, self._field)

        # Do not report improvement if risk rose since the last attempt.
        if risk_score > previous:
            return None

        if previous - risk_score >= 10:
            return (
                f"Your {self._label} risk score has improved since "
                "your last attempt. Keep it up!"
            )

        average = history.get_average(self._field)

        if average - risk_score >= 10:
            return (
                f"Your {self._label} risk score has improved compared "
                "with your previous average. Keep it up!"
            )

        return None