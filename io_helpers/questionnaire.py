'''
Survey Questions
'''

from io_helpers.prompts import RangePrompt, ChoicePrompt, TextPrompt
from io_helpers.survey_response import SurveyResponse


# Originally prompt_questionnaire()
class Questionnaire:
    MOOD_OPTIONS = ("Motivated", "Calm", "Anxious", "Sad", "Exhausted")
    REFLECTION_LIMIT = 500      #Character limit for freeform reflection

    # CHANGED: no questions parameter. SurveyResponse needs exactly these questions, so any other list crashed
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
            ("mood", ChoicePrompt(cls.MOOD_OPTIONS,
                                  "Select your mood from the following options:",
                                  "Enter the number corresponding to your mood: ")),
            ("social_activity_level", cls._scale("how socially active have you been")),
            ("reflection", TextPrompt(
                "Reflection: ", cls.REFLECTION_LIMIT,
                f"Please enter a reflection with at most {cls.REFLECTION_LIMIT} characters.")),
        ]

    # e.g. "sleep_duration" -> "Sleep Duration"
    @staticmethod
    def heading(key):
        return key.replace('_', ' ').title()

    # Ask every question and return the answers as a SurveyResponse (None if cancelled)
    def run(self, user_id):    # CHANGED: user_id is required, so every SurveyResponse belongs to a user
        responses = {
            "user_id": user_id
        }
        try:
            for i, (key, prompt) in enumerate(self.questions, start=1):
                print(f"\n{i}. {self.heading(key)}")
                responses[key] = prompt.ask()
            return SurveyResponse.from_dict(responses)    # Parses responses into SurveyResponse object
        except (KeyboardInterrupt, EOFError):
            print("\n\nSurvey cancelled.")
            return None