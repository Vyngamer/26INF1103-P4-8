'''
Survey Answers Error
'''

from invalid_input import InvalidInput
from io_helpers.questionnaire import Questionnaire


# Raised by Questionnaire.from_answers() when any answer is invalid.
# errors maps each invalid question key to its problem, in question order
class SurveyAnswersError(InvalidInput):
    def __init__(self, errors):
        self.errors = dict(errors)
        super().__init__("; ".join(f"{Questionnaire.heading(key)}: {problem}"
                                   for key, problem in self.errors.items()))