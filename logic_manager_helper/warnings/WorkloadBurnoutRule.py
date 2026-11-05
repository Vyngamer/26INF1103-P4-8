from .WarningRule import WarningRule
from ..CurrentAttempt import CurrentAttempt

class WorkloadBurnoutRule(WarningRule):
    def evaluate(self, current: CurrentAttempt) -> str | None:
        if current.burnout_risk_score > 60 and current.academic_workload >= 7:
            return "Burnout Warning (Workload)"
        return None