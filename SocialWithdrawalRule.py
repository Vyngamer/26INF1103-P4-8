from WarningRule import WarningRule
from CurrentAttempt import CurrentAttempt

class SocialWithdrawalRule(WarningRule):
    def evaluate(self, current: CurrentAttempt) -> str | None:
        if current.social_activity_level <= 3 and current.sentiment == "Negative":
            return "Social Withdrawal Risk"
        return None