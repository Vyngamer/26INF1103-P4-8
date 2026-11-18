import json

import pytest

from ai_manager import AIManager
from ai_manager_helper.crisis_safety_filter import CrisisDetectedError, CrisisSafetyFilter
from ai_manager_helper.data_classes.ai_output import AIOutput
from ai_manager_helper.data_classes.survey_entity_schema import SurveyEntitySchema
from tests.support.survey_payload_builder import SurveyPayloadBuilder


class TestSurveyTurn:
    """process_message with the survey-collection strategy."""

    def test_returns_the_model_reply_and_survey_flag(self, ai_manager, responder, collect_strategy):
        responder.push(SurveyPayloadBuilder(text="How many hours did you sleep?", survey_done=False).build())

        reply = ai_manager.process_message("Hello!", collect_strategy)

        assert reply == {"text": "How many hours did you sleep?", "survey_done": False}

    def test_reports_survey_done_when_the_model_says_so(self, ai_manager, responder, collect_strategy):
        responder.push(SurveyPayloadBuilder(survey_done=True).build())
        assert ai_manager.process_message("That's all", collect_strategy)["survey_done"] is True

    def test_sends_the_strategy_instruction_and_schema(self, ai_manager, responder, mock_client, collect_strategy):
        responder.push(SurveyPayloadBuilder().build())

        ai_manager.process_message("Hello!", collect_strategy)

        sent = mock_client.last
        assert sent.prompt == "Hello!"
        assert sent.system_instruction == collect_strategy.get_system_instruction()
        assert sent.json_response_schema == collect_strategy.get_json_response_schema()

    def test_keeps_the_latest_answers_for_show_survey_results(self, ai_manager, responder, collect_strategy):
        responder.push(SurveyPayloadBuilder(sleep_duration=5.0).build(),
                       SurveyPayloadBuilder(sleep_duration=6.5).build())

        ai_manager.process_message("I slept 5 hours", collect_strategy)
        ai_manager.process_message("Actually 6.5", collect_strategy)

        assert ai_manager.show_survey_results()["sleep_duration"] == 6.5