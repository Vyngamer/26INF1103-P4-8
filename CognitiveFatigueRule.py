from WarningRule import WarningRule
from CurrentAttempt import CurrentAttempt

class CognitiveFatigueRule(WarningRule):
    def evaluate(self, current: CurrentAttempt) -> str | None:
        if current.focus_level <= 4 and current.sentiment == "Negative":
            return "Cognitive Fatigue Risk"
        return None