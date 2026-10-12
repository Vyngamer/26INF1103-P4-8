import pytest
import os
from ai_manager import valid_survey, call_api

valid_survey_false = [
    {},
    {'asdfasd':'asdfasdf'},
    {
    "user_id": 1,
    "sleep_duration": 9,
    "stress_level": 2,
    "focus_level": 2,
    "academic_workload": 9,
    "mood": "Exhausted",
    "social_activity_level": 3,
    }
]

# test valid_survey false cases
@pytest.mark.parametrize('survey_data', valid_survey_false)
def test_valid_survey_false(survey_data):
    assert valid_survey(survey_data) is False

valid_survey_true = [
    {
        "user_id": 1,
        "sleep_duration": 9,
        "stress_level": 2,
        "focus_level": 2,
        "academic_workload": 9,
        "mood": "Exhausted",
        "social_activity_level": 3,
        "reflection": "im feeling too stressed already"
    }
]
# test valid_survey true cases
@pytest.mark.parametrize('survey_data', valid_survey_true)
def test_valid_survey_true(survey_data):
    assert valid_survey(survey_data) is True 

# check if the Gemini API key exists
def test_api_key_exists():
    assert len(os.environ["GEMINI_API_KEY"]) != 0

call_api_test_data = [
        ("", "", {}, None, "gemini-3.1-flash-lite")
]
# test if the call_api function works
@pytest.mark.parametrize('prompt, system_instruction, response_output_format, previous_interaction_id, model', call_api_test_data)
def test_call_api(prompt, system_instruction, response_output_format, previous_interaction_id, model):
    assert not isinstance(call_api(prompt, system_instruction, response_output_format, previous_interaction_id, model), Exception)
