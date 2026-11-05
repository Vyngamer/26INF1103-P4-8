from .ComparisonRule import ComparisonRule
from ..CurrentAttempt import CurrentAttempt
from ..PreviousAttempts import PreviousAttempts

class SleepComparison(ComparisonRule):
    def evaluate(
        self,
        current: CurrentAttempt,
        history: PreviousAttempts,
    ) -> str | None:
        average = history.get_average("sleep_duration")

        if average is None:
            return None

        difference = average - current.sleep_duration

        if difference > 0:
            return f"You slept {difference:.2f} hours less than your average."

        if difference < 0:
            return f"You slept {abs(difference):.2f} hours more than your average."

        return "You slept the same number of hours as your average."