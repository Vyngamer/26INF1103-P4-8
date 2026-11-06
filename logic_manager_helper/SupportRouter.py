from .CurrentAttempt import CurrentAttempt

class SupportRouter:
    def decide(self, current: CurrentAttempt, tier: str, warnings: list[str]) -> str:
        if current.crisis_alert:
            return "Urgent support"
        combined_risk = (
            current.mental_wellness_risk_score >= 60
            and current.burnout_risk_score >= 70
            and current.sentiment == "Negative"
            )
        if tier == "High" or len(warnings) >= 2 or combined_risk:
            return "Counsellor follow-up"
        return "Self-care guidance"