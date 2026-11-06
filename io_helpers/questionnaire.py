'''
Survey Questions
'''

from abc import ABC, abstractmethod
from io_helpers.prompts import RangePrompt, ChoicePrompt, LimitedTextPrompt

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
    def ask(self):
        return self.make_prompt().ask()

    #Build and return the Prompt used to ask this question
    @abstractmethod
    def make_prompt(self):
        pass


# Originally get_sleep_duration()
# Avg daily sleep hours in the past week (0-24)
class SleepQuestion(Question):
    def __init__(self, key="sleep_duration"):
        super().__init__(key)

    def make_prompt(self):
        return RangePrompt("How many hours per day did you sleep on average for the past week?: ",
                           0, 24, cast=float)


# Originally scale_question()
# Generic 1-10 numerical scale question
class ScaleQuestion(Question):
    def __init__(self, key, description):
        super().__init__(key)
        self.description = description

    def make_prompt(self):
        return RangePrompt(f"On a scale of 1-10, {self.description} for the past week?: ", 1, 10)


# Originally get_mood()
# Mood selection from predefined options
class MoodQuestion(Question):
    MOOD_OPTIONS = ("Motivated", "Calm", "Anxious", "Sad", "Exhausted")

    def __init__(self, key="mood"):
        super().__init__(key)

    def make_prompt(self):
        return ChoicePrompt(self.MOOD_OPTIONS,
                            "Select your mood from the following options:",
                            "Enter the number corresponding to your mood: ")


# Originally get_reflection()
# Free-response reflection with a length limit
class ReflectionQuestion(Question):
    def __init__(self, key="reflection", limit=500):
        super().__init__(key)
        self.limit = limit

    def make_prompt(self):
        return LimitedTextPrompt("Reflection: ", self.limit,
                                 f"Please enter a reflection with at most {self.limit} characters.")


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