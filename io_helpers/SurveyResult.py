'''
Survey Result
'''

from dataclasses import dataclass, field
from io_helpers.SurveyResponse import SurveyResponse

# Returned by IOManager.survey(). ok = True if valid answer, else False;
# errors then map each invalid question key to its problem (see Questionnaire.from_answers)
@dataclass
class SurveyResult:
    result: bool
    message: str
    response: SurveyResponse = None
    errors: dict = field(default_factory=dict)