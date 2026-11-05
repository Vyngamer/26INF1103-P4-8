class CurrentAttempt:
    """Hold the user and AI values needed for the current assessment."""

    def __init__(
        self,
        sleep_duration: float,
        academic_workload: int,
        social_activity_level: int,
        focus_level: int,
        mental_wellness_risk_score: int,
        burnout_risk_score: int,
        sentiment: str,
        crisis_alert: bool,
    ):
        self._sleep_duration = sleep_duration
        self._academic_workload = academic_workload
        self._social_activity_level = social_activity_level
        self._focus_level = focus_level
        self._mental_wellness_risk_score = mental_wellness_risk_score
        self._burnout_risk_score = burnout_risk_score
        self._sentiment = sentiment
        self._crisis_alert = crisis_alert

    @property
    def sleep_duration(self) -> float:
        return self._sleep_duration

    @property
    def academic_workload(self) -> int:
        return self._academic_workload

    @property
    def social_activity_level(self) -> int:
        return self._social_activity_level

    @property
    def focus_level(self) -> int:
        return self._focus_level

    @property
    def mental_wellness_risk_score(self) -> int:
        return self._mental_wellness_risk_score

    @property
    def burnout_risk_score(self) -> int:
        return self._burnout_risk_score

    @property
    def sentiment(self) -> str:
        return self._sentiment

    @property
    def crisis_alert(self) -> bool:
        return self._crisis_alert