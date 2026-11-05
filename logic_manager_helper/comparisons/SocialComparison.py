from .ComparisonRule import ComparisonRule
from ..CurrentAttempt import CurrentAttempt
from ..PreviousAttempts import PreviousAttempts

class SocialComparison(ComparisonRule):
    def evaluate(
        self,
        current: CurrentAttempt,
        history: PreviousAttempts,
    ) -> str | None:
        values = history.get_values("social_activity_level")

        if not values:
            return None

        # Three drops across the last three attempts and this attempt.
        if len(values) >= 3:
            first, second, third = values[-3:]

            consecutive_drop = (
                first - second >= 1
                and second - third >= 1
                and third - current.social_activity_level >= 1
            )

            if consecutive_drop:
                return (
                    "Your social activity has dropped across four "
                    "consecutive attempts. Try connecting with others."
                )

        average = history.get_average("social_activity_level")

        if average - current.social_activity_level >= 2:
            return (
                "You are socialising less than your previous average. "
                "Try connecting with others."
            )

        return None