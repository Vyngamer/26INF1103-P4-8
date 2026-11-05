from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, ValidationError, field_validator

@dataclass(frozen=True)
class APIResult(Generic[TypeVar('T'), TypeVar('E')]):
    success: bool
    data: Optional[T] = None
    error: Optional[E] = None

    @classmethod
    def ok(cls, data):
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error):
        return cls(success=False, error=error)


class SurveyEntitySchema(BaseModel):
    sleep_duration: int = Field(gte=-1, lte=24, description="Average daily sleep hours over past week (0-24), The user had {sleep} hours of sleep")
    stress_level: int = Field(gte=-1, lte=10, description="Current stress (1 = Very Low, 10 = Very High), the user's stress level is {stress} out of 10")
    focus_level: int = Field(gte=-1, lte=5, description="Ability to concentrate (1 = Very Poor, 5 = Excellent), the user's focus level is {focus} out of 10")
    academic_workload: int = Field(gte=-1, lte=10, description="Coursework load (1 = Light, 10 = Very Heavy), the user's academic workload is {workload} out of 10")
    mood: Literal['Motivated', 'Calm', 'Anxious', 'Sad', 'Exhausted', 'Undefined'] = \
            Field(description="Emotional state, the user's mood is {mood}")
    social_activity_level: int = \
            Field(gte=-1, lte=10, description="Engagement level (1 = Isolated, 10 = Very Social), the user's social activity level is {social} out of 10")
    reflection: str = Field(description="Free-response text capturing personal thoughts/concerns, the user's reflection text is {reflection}.")
    text: str = Field(description="A question to prompt the user on any of these fields.")

    model_config = ConfigDict(extra='forbid', strict=True)

    def validate_response(response):
        try:
            SurveyEntitySchema(**response)

        except ValidationError as e:
            print(e)
            return False
        
        return True
    
    @field_validator('focus_level', 'stress_level', 'sleep_duration', 'social_activity_level', 'academic_workload')
    def not_negative_or_zero(cls, value):
        if value < 1:
            raise ValueError(f'{value} is not valid.')
        return value

    @field_validator('reflection', 'text')
    def text_not_empty(cls, text):
        if text == "" or text == "None":
            raise ValueError(f'{text} not valid')
        return text

