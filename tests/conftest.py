"""Fixtures for the AI-manager tests. AIManager is always built with a MockChatClient."""

import pytest

from ai_manager import AIManager
from ai_manager_helper.collect_survey_strategy import CollectSurveyStrategy
from ai_manager_helper.evaluate_survey_strategy import EvaluateSurveyStrategy

@pytest.fixture
def ai_manager(mock_client, safety_filter) -> AIManager:
    # Dependency Inversion: AIManager receives its client and filter, so tests hand it doubles.
    return AIManager(client=mock_client, safety_filter=safety_filter)


@pytest.fixture
def collect_strategy() -> CollectSurveyStrategy:
    return CollectSurveyStrategy()


@pytest.fixture
def evaluate_strategy() -> EvaluateSurveyStrategy:
    return EvaluateSurveyStrategy()
