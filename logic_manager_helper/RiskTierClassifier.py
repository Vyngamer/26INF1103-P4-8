from .CurrentAttempt import CurrentAttempt

class RiskTierClassifier:
    """Classifies the risk tier of a current attempt based on its attributes."""
    def classify(self, current: CurrentAttempt) -> str:
        score = current.mental_wellness_risk_score
        if current.score < 50:
            return "High Risk"
        elif 50 <= current.score < 75:
           return "Medium Risk"
        else:
            return "Low Risk"