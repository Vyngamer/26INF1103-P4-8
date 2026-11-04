'''
Survey Questions
'''

from abc import ABC, abstractmethod
from prompts import RangePrompt, ChoicePrompt, LimitedTextPrompt

# Abstract base class for one survey question. Each question knows the
# key its answer is stored under and how to ask for that answer.
class Question(ABC):
    def __init__(self, key):
        self.key = key

    #Heading shown above the question, e.g. "sleep_duration" -> "Sleep Duration"
    @property
    def heading(self):
        return self.key.replace('_', ' ').title()

    #Ask the question and return the validated answer
    @abstractmethod
    def ask(self):
        pass


# Originally get_sleep_duration()
# Avg daily sleep hours in the past week (0-24)
class SleepQuestion(Question):
    def __init__(self, key="sleep_duration"):
        super().__init__(key)

    def ask(self):
        return RangePrompt("How many hours per day did you sleep on average for the past week?: ",
                           0, 24, cast=float).ask()


# Originally scale_question()
# Generic 1-10 numerical scale question
class ScaleQuestion(Question):
    def __init__(self, key, description):
        super().__init__(key)
        self.description = description

    def ask(self):
        return RangePrompt(f"On a scale of 1-10, {self.description} for the past week?: ", 1, 10).ask()


# Originally get_mood()
# Mood selection from predefined options
class MoodQuestion(Question):
    MOOD_OPTIONS = ["Motivated", "Calm", "Anxious", "Sad", "Exhausted"]

    def __init__(self, key="mood"):
        super().__init__(key)

    def ask(self):
        return ChoicePrompt(self.MOOD_OPTIONS,
                            "Select your mood from the following options:",
                            "Enter the number corresponding to your mood: ").ask()


# Originally get_reflection()
# Free-response reflection with a length limit
class ReflectionQuestion(Question):
    def __init__(self, key="reflection", limit=500):
        super().__init__(key)
        self.limit = limit

    def ask(self):
        return LimitedTextPrompt("Reflection: ", self.limit,
                                 f"Please enter a reflection with at most {self.limit} characters.").ask()


# Originally prompt_questionnaire(). Holds the ordered list of Question objects.
class Questionnaire:
    def __init__(self, questions=None):
        if questions is None:
            questions = [
                SleepQuestion(),
                ScaleQuestion("stress_level", "how stressed have you been"),
                ScaleQuestion("focus_level", "how focused have you been"),
                ScaleQuestion("academic_workload", "how heavy has your academic workload been"),
                MoodQuestion(),
                ScaleQuestion("social_activity_level", "how socially active have you been"),
                ReflectionQuestion()
            ]
        self.questions = list(questions)

    #Ask every question and return a dictionary of responses (None if cancelled)
    def run(self):
        responses = {
            "user_id": None
        }
        try:
            for i, question in enumerate(self.questions, start=1):
                print(f"\n{i}. {question.heading}")
                responses[question.key] = question.ask()
            return responses
        except (KeyboardInterrupt, EOFError):
            print("\n\nSurvey cancelled.")
            return None

'''
class AssessmentResults:
    def __init__(self, results):
        self.results = results

    #Load from json (empty results if the file is missing or invalid)
    @classmethod
    def load(cls, filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return cls(json.load(file))
        except (FileNotFoundError, json.JSONDecodeError):
            return cls({})

    #Output AI and logic results to the user (was risk_assessment)
    def display(self):
        results = self.results
        print("\n--- Mental Health Assessment Results ---")
        #AI risk score & risk tier
        print(f"Mental Wellness Risk Score: {results.get('mental_wellness_risk_score', 'N/A')} / 100 "
              f"({results.get('mental_wellness_risk_tier', 'Unknown')} Risk)")
        #Burnout risk score
        print(f"Burnout Risk Score: {results.get('burnout_risk_score', 'N/A')} / 100")
        #Primary stressors
        print(f"Primary Stressor: {results.get('primary_stressor', 'N/A')}")
        #Note to self: Check if there may be multiple stressors

        #Recommendations
        print(f"\nRecommendation(s):\n{results.get('personalized_recommendations', 'None')}\n")

        #Warnings
        warnings = results.get("warnings", [])
        if warnings:
            print("Please heed these warning(s):")
            print("\n".join(warnings))
            print()

        #Crisis alert
        if results.get("crisis_alert"):
            print("!! You may be in crisis. Please contact a crisis helpline or emergency services now,")
            print("   or reach out to someone you trust. You do not have to go through this alone.\n")

        #Suggest counseling if needed
        if results.get("counselling_recommendation"):
            print("Alert: You are advised to seek counseling.\n")
'''