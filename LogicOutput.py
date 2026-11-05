class LogicOutput:
    def __init__(self, mental_wellness_risk_tier: str, warnings: list[str], route: str, display_messages: list[str]):
        self._mental_wellness_risk_tier = mental_wellness_risk_tier
        self._warnings = warnings.copy()
        self._route = route
        self._display_messages = display_messages.copy()
    
    @property
    def mental_wellness_risk_tier(self) -> str:
        return self._mental_wellness_risk_tier
    
    @property
    def warnings(self) -> list[str]:
        return self._warnings.copy()
    
    @property
    def route(self) -> str:
        return self._route
    
    @property
    def counselling_recommendation(self) -> bool:
        return self._route in (
            "Urgent support",
            "Counsellor follow-up",
        )
    
    @property
    def display_messages(self) -> list[str]:
        return self._display_messages.copy()
    
    def to_dict(self) -> dict:
        return {
            "mental_wellness_risk_tier": self.mental_wellness_risk_tier,
            "warnings": self.warnings,
            "route": self.route,
            "counselling_recommendation": self.counselling_recommendation,
            "display_messages": self.display_messages,
        }