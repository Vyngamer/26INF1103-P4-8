'''
Survey Answers Error
'''

from io_helpers.errors.invalid_input import InvalidInput


# Raised by Questionnaire.from_answers() when any answer is invalid.
# errors maps each invalid question key to its problem, in question order
class SurveyAnswersError(InvalidInput):
    def __init__(self, errors):
        self.errors = dict(errors)
        super().__init__("; ".join(f"{key.replace('_', ' ').title()}: {problem}"
                                   for key, problem in self.errors.items()))