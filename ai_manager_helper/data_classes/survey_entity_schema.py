from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, ValidationError, field_validator


class SurveyEntitySchema(BaseModel):
    sleep_duration: int = Field(alias="Sleep duration" ,gte=-1, lte=24, description="Average daily sleep hours over past week (0-24), The user had {sleep} hours of sleep")
    stress_level: int = Field(alias="Stress level" ,gte=-1, lte=10, description="Current stress (1 = Very Low, 10 = Very High), the user's stress level is {stress} out of 10")
    focus_level: int = Field("Focues level", gte=-1, lte=10, description="Ability to concentrate (1 = Very Poor, 10 = Excellent), the user's focus level is {focus} out of 10")
    academic_workload: int = Field("Academic workload", gte=-1, lte=10, description="Coursework load (1 = Light, 10 = Very Heavy), the user's academic workload is {workload} out of 10")
    mood: Literal['Motivated', 'Calm', 'Anxious', 'Sad', 'Exhausted', 'Undefined'] = \
            Field("Mood", description="Emotional state, the user's mood is {mood}")
    social_activity_level: int = \
            Field("Social activity level", gte=-1, lte=10, description="Engagement level (1 = Isolated, 10 = Very Social), the user's social activity level is {social} out of 10")
    reflection: str = Field("Reflection", description="Free-response text capturing personal thoughts/concerns, the user's reflection text is {reflection}.")
    text: str = Field(description="A question to prompt the user on any of these fields.")
    survey_done: bool = Field(description="A True or False signal which tells the program that all the survey fields have been collected and is verified to be correct both in data type and range.")

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
        if not 1 <= value <= 10: 
            raise ValueError(f'{value} is not valid.')
        return value

    @field_validator('reflection', 'text')
    def text_not_empty(cls, text):
        if text == "" or text == "None":
            raise ValueError(f'{text} not valid')
        return text
