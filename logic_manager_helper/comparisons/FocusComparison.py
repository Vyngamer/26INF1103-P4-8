from .ComparisonRule import ComparisonRule
from ..CurrentAttempt import CurrentAttempt
from ..PreviousAttempts import PreviousAttempts

class FocusComparison(ComparisonRule):
    def evaluate(
        self,
        current: CurrentAttempt,
        history: PreviousAttempts,
    ) -> str | None:
        previous = history.get_latest("focus_level")

        if previous is None:
            return None

        focus = current.focus_level

        # The latest attempt takes priority over the historical average.
        if previous - focus >= 2:
            return (
                "Your focus level has dropped since your last attempt. "
                "Try taking a break and resting."
            )

        if focus - previous >= 1:
            return (
                "Your focus level has improved since your last attempt. "
                "Keep it up!"
            )

        average = history.get_average("focus_level")

        if average - focus >= 2:
            return (
                "Your focus level is below your previous average. "
                "Try taking a break and resting."
            )

        if focus - average >= 1:
            return (
                "Your focus level has improved compared with your "
                "previous average. Keep it up!"
            )

        return None