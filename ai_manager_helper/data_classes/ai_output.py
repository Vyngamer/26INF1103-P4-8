class AIOutput:
    def __init__(self, mental_wellness_risk_score: int, sentiment: str, burnout_risk_score: int, crisis_alert: bool, primary_stressor: str, personalized_recommendations: str):
        self.mental_wellness_risk_score = mental_wellness_risk_score
        self.sentiment = sentiment
        self.burnout_risk_score = burnout_risk_score
        self.crisis_alert = crisis_alert
        self.primary_stressor = primary_stressor
        self.personalized_recommendations = personalized_recommendations