from .WarningRule import WarningRule
from ..CurrentAttempt import CurrentAttempt

class SleepBurnoutRule(WarningRule):
    def evaluate(self, current: CurrentAttempt) -> str | None:
        if current.burnout_risk_score > 75 and current.sleep_duration < 6:
            return "High Burnout Warning (Sleep)"
        return None