from .CurrentAttempt import CurrentAttempt

class RiskTierClassifier:
    """Classifies the risk tier of a current attempt based on its attributes."""
    def classify(self, current: CurrentAttempt) -> str:
        score = current.mental_wellness_risk_score
        if score >= 71:
            return "High"
        elif score >= 41:
           return "Medium"
        else:
            return "Low"