from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, ValidationError, field_validator
from google import genai
import sys
import os
import json
import google
from google.genai._gaos.lib.compat_errors import APIConnectionError, NotFoundError
from ai_error_handler import APIErrorHandler

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


class GeminiClient:
    def __init__(self, model, system_instruction=None, response_json_format=None):
        self._model = model
        self._system_instruction = system_instruction
        self._response_json_format = response_json_format
        self._client = None
        self._previous_interaction_id = None
    
    def generate_response_format(self, json_response_format):
        response_format = None

        if self._response_json_format:
            response_format = {
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": self._response_json_format
                }

        return response_format

    def set_previous_interaction_id(self, id):
        self._previous_interaction_id = id

    @APIErrorHandler.general_error_handler
    @APIErrorHandler.failed_api_key_handler
    def connect_client(self):
        self._client = genai.Client()

    @APIErrorHandler.general_error_handler
    @APIErrorHandler.backup_model_retry
    @APIErrorHandler.failed_api_key_handler
    @APIErrorHandler.failed_network_handler
    def call_api(self, prompt):
        response_format = self.generate_response_format(self._response_json_format)

        try: 
            interaction = self._client.interactions.create(
                    model=self._model,
                    input=prompt,
                    system_instruction=self._system_instruction,
                    previous_interaction_id=self._previous_interaction_id,
                    response_format=response_format
                )
            
            self._previous_interaction_id = interaction.id
            print(interaction)
            return APIResult.ok(interaction.output_text)

        except Exception as e:
            return APIResult.fail(e)


class AICounsellor(GeminiClient):
    def __init__(self):
        system_instruction = """
                You are an expert student counselor and psychological assessment AI specializing in adolescent 
                and higher education mental health. Your job is to conduct a survey to collect information on these fields: 
                - Sleep Duration: Average daily sleep hours over past week (0-24), The user had {sleep} hours of sleep. -1
                for undefined
                - Stress Level: Current stress (1 = Very Low, 10 = Very High), the user's stress level is {stress} out of 10.
                -1 for undefined 
                - Focus Level: Ability to concentrate (1 = Very Poor, 5 = Excellent), the user's focus level is {focus} out 
                of 10. -1 for undefined
                - Academic Workload: Coursework load (1 = Light, 10 = Very Heavy), the user's academic workload is {workload}
                out of 10. -1 for undefined
                - Mood for the Day: Emotional state ["Motivated", "Calm", "Anxious", "Sad", "Exhausted", "Undefined"], the 
                user's mood is {mood}. -1 for undefined
                - Social Activity Level: Engagement level (1 = Isolated, 10 = Very Social), the user's social activity level 
                is {social} out of 10. "Undefined" for undefined.
                - Reflection: Free-response text capturing personal thoughts/concerns, the user's reflection text is {reflection}.

                You are to be affable, kind, and conversational when conducting this survey.

                Identify the entities defined in the response json format and do not guess. If the user is not clear
                in any of the data fields then do not change the fields. For example, if the user mentions that 
                he/she only had 5 hours of sleep on average, then only fill in the json response for sleep duration.

                The fields are quantitative, so only fill them in when the user explicitly states the field value. If 
                the user vaguely answers the questions without providing a valid data value then re-prompt the question.

                Strictly adhere to the range stated within the fields. If the user uses hyperbole then default to the 
                corresponding end of the range.
            """

        model = "gemini-3.5-flash-lite"

        response_json_format = SurveyEntitySchema.model_json_schema()

        super().__init__(model, system_instruction, response_json_format=response_json_format)


