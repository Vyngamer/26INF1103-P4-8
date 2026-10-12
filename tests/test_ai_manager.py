import pytest
from ai_manager import call_api, generate_prompt, generate_survey_response


# test call_api(prompt, system_instruction, response_output_format, previous_interaction_id)
@pytest.mark.parametrize("input_value", "expected_output", [
    (("", "", {}), None), 200
])
def test_call_api(input_value, expected_output):
     

# test generate_prompt(survey_data)
@pytest.mark.parametrize("input_value", "expected_output", [
    ({}, "")
])
def test_generate_prompt(input_value, expected_output):
    assert generate_prompt(*input_value) == expected_output

# test generate_survey_response(survey_data, previous_interaction_id=None)
@pytest.mark.parametrize("input_value", "expected_output", [
    ({}, "")
])
def test_generate_survey_response():
    pass
