import pytest
import os
from ai_manager import validate_response, call_api, generate_survey_response

valid_survey_false = [
    {},
    {'asdfasd':'asdfasdf'},
    {
    "user_id": 1,
    "sleep_duration": 9.0,
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
    assert validate_response(survey_data) is False

valid_survey_true = [
    {
        "burnout_risk_score": 50,
        "crisis_alert": True,
        "mental_wellness_risk_score": 85,
        "personalized_recommendations": "Your sleep duration of only one hour is critically low and poses an immediate danger to your physical and cognitive health. Please prioritize immediate rest or contact a medical professional, as your current level of sleep deprivation is unsustainable and requires urgent attention.",
        "primary_stressor": "Sleep Deprivation",
        "sentiment": "Neutral"
    }
]
# test valid_survey true cases
@pytest.mark.parametrize('survey_data', valid_survey_true)
def test_valid_survey_true(survey_data):
    assert validate_response(survey_data) is True 

# check if the Gemini API key exists
def test_api_key_exists():
    assert len(os.environ["GEMINI_API_KEY"]) != 0


call_api_test_data = [
    ("Hello!", "", {}, None )
]
# test if the call_api function works
@pytest.mark.parametrize('prompt, system_instruction, response_output_format, previous_interaction_id', call_api_test_data)
def test_call_api(prompt, system_instruction, response_output_format, previous_interaction_id):
    try:
        interaction = call_api(prompt, system_instruction, response_output_format, previous_interaction_id)
        assert True
    except SystemExit:
        assert False

call_api_test_data_xfail = [
    ("Hello!", "", {}, None, None)
]
@pytest.mark.parametrize('prompt, system_instruction, response_output_format, previous_interaction_id, model', call_api_test_data_xfail)
def test_call_api_xfail(prompt, system_instruction, response_output_format, previous_interaction_id, model):
    try:
        interaction = call_api(prompt, system_instruction, response_output_format, previous_interaction_id, model=model)
        assert False
    except Exception as e:
        assert True 



