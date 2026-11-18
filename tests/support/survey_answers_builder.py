from __future__ import annotations

from tests.support.builders import Builder

class SurveyAnswersBuilder(Builder[dict]):
    """Raw survey answers as the web app passes them to IOManager.survey (no user id)."""

    DEFAULTS = {
        "sleep_duration": 7.5,
        "stress_level": 5,
        "focus_level": 6,
        "academic_workload": 4,
        "mood": "Calm",
        "social_activity_level": 6,
        "reflection": "Good week",
    }

    def build(self) -> dict:
        return self.values()