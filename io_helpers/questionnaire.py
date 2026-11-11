'''
Survey Questions
'''

from io_helpers.prompts import RangePrompt, ChoicePrompt, TextPrompt, InvalidInput
from io_helpers.survey_response import SurveyResponse


# Raised by Questionnaire.from_answers() when any answer is invalid.
# errors maps each invalid question key to its problem, in question order
class SurveyAnswersError(InvalidInput):
    def __init__(self, errors):
        self.errors = dict(errors)
        super().__init__("; ".join(f"{Questionnaire.heading(key)}: {problem}"
                                   for key, problem in self.errors.items()))


# Questionnaire class
class Questionnaire:
    MOOD_OPTIONS = ("Motivated", "Calm", "Anxious", "Sad", "Exhausted")
    REFLECTION_LIMIT = 500      #Character limit for freeform reflection

    def __init__(self):
        self.questions = self.default_questions()

    # Builds a 1-10 scale prompt
    @staticmethod
    def _scale(description):
        return RangePrompt(f"On a scale of 1-10, {description} for the past week?: ", 1, 10)

    # Default survey questions as (key, prompt) pairs
    @classmethod
    def default_questions(cls):
        return [
            ("sleep_duration", RangePrompt(
                "How many hours per day did you sleep on average for the past week?: ", 0, 24, cast=float)),
            ("stress_level", cls._scale("how stressed have you been")),
            ("focus_level", cls._scale("how focused have you been")),
            ("academic_workload", cls._scale("how heavy has your academic workload been")),
            ("mood", ChoicePrompt(cls.MOOD_OPTIONS, "Select your mood from the following options:")),
            ("social_activity_level", cls._scale("how socially active have you been")),
            ("reflection", TextPrompt(
                "Reflection: ", cls.REFLECTION_LIMIT,
                f"Please enter a reflection with at most {cls.REFLECTION_LIMIT} characters.")),
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