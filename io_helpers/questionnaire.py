'''
Survey Questions
'''

from io_helpers.prompt_range import RangePrompt
from io_helpers.prompt_choice import ChoicePrompt
from io_helpers.prompt_text import TextPrompt
from io_helpers.errors.invalid_input import InvalidInput
from io_helpers.survey_response import SurveyResponse
from io_helpers.errors.survey_error import SurveyAnswersError


# Questionnaire class
class Questionnaire:
    MOOD_OPTIONS = ("Motivated", "Calm", "Anxious", "Sad", "Exhausted")
    REFLECTION_LIMIT = 500      #Character limit for freeform reflection

    def __init__(self):
        self.questions = self.default_questions()

    # Default survey questions as (key, answer check) pairs
    @classmethod
    def default_questions(cls):
        return [
            ("sleep_duration", RangePrompt(0, 24, cast=float)),
            ("stress_level", RangePrompt(1, 10)),
            ("focus_level", RangePrompt(1, 10)),
            ("academic_workload", RangePrompt(1, 10)),
            ("mood", ChoicePrompt(cls.MOOD_OPTIONS)),
            ("social_activity_level", RangePrompt(1, 10)),
            ("reflection", TextPrompt(
                cls.REFLECTION_LIMIT, f"Please enter a reflection with at most {cls.REFLECTION_LIMIT} characters.")),
        ]

    # e.g. "sleep_duration" -> "Sleep Duration"
    @staticmethod
    def heading(key):
        return key.replace('_', ' ').title()

    # Checks answers passed in (e.g. the web chatbot's survey results)
    # Answers maps each question key to its answer, other keys are ignored, missing answer counts as empty.
    # Returns the answers as a SurveyResponse, or raises SurveyAnswersError listing every invalid answer
    def from_answers(self, user_id, answers):
        answers = answers or {}    # No answers at all counts as every answer empty
        responses = {
            "user_id": user_id
        }
        errors = {}    # Errors found so far, by question key
        for key, prompt in self.questions:
            try:
                responses[key] = prompt.parse(answers.get(key))
            except InvalidInput as problem:    # Note error and check remaining answers
                errors[key] = str(problem)
        if errors:
            raise SurveyAnswersError(errors)
        return SurveyResponse.from_dict(responses)    # Parses responses into SurveyResponse object