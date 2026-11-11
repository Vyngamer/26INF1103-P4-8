'''
One completed survey's answers
'''

from dataclasses import dataclass, asdict, field


# Returned by Questionnaire.from_answers()
# User ID + Responses for each survey question
@dataclass
class SurveyResponse:
    user_id: str
    sleep_duration: float          # hours, 0-24
    stress_level: int              # 1-10
    focus_level: int               # 1-10
    academic_workload: int         # 1-10
    mood: str                      # one of Questionnaire.MOOD_OPTIONS
    social_activity_level: int     # 1-10
    reflection: str                # free text, max characters set in Questionnaire.REFLECTION_LIMIT in questionnaire.py

    # Build a SurveyResponse from a dictionary
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    # Parse to dictionary
    def to_dict(self):
        return asdict(self)


# Returned by IOManager.survey(). ok = True if valid answer, else False;
# errors then map each invalid question key to its problem (see Questionnaire.from_answers)
@dataclass
class SurveyResult:
    ok: bool
    message: str
    response: SurveyResponse = None
    errors: dict = field(default_factory=dict)