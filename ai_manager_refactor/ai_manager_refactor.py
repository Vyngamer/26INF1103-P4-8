from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Any, Literal
from pydantic import BaseModel, Field
from google import genai
import sys
import os
import json
import google
from google.genai._gaos.lib.compat_errors import APIConnectionError, NotFoundError
from ai_manager_helper import general_error_handler, backup_model_retry, failed_network_handler, failed_api_key_handler

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
    sleep_duration: int = Field(description="Average daily sleep hours over past week (0-24), The user had {sleep} hours of sleep")
    stress_level: int = Field(description="Current stress (1 = Very Low, 10 = Very High), the user's stress level is {stress} out of 10")
    focus_level: int = Field(description="Ability to concentrate (1 = Very Poor, 5 = Excellent), the user's focus level is {focus} out of 10")
    academic_workload: int = Field(description="Coursework load (1 = Light, 10 = Very Heavy), the user's academic workload is {workload} out of 10")
    mood: Literal['Motivated', 'Calm', 'Anxious', 'Sad', 'Exhausted'] = \
            Field(description="Emotional state, the user's mood is {mood}")
    social_activity_level: int = Field(description="Engagement level (1 = Isolated, 10 = Very Social), the user's social activity level is {social} out of 10")
    reflection: str = Field(description="Free-response text capturing personal thoughts/concerns, the user's reflection text is {reflection}.")


class GeminiClient:
    def __init__(self, model, system_instruction=None, response_json_format=None):
        self._model = model
        self._system_instruction = system_instruction
        self._response_json_format = response_json_format
        self._client = None
        self._previous_interaction_id = None
    
    @general_error_handler
    @failed_api_key_handler
    def connect_client(self):
        self._client = genai.Client()

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

    @general_error_handler
    @backup_model_retry
    @failed_api_key_handler
    @failed_network_handler
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
            return APIResult.ok(interaction.output_text)

        except Exception as e:
            return APIResult.fail(e)


class AICounsellor(GeminiClient):
    def __init__(self):
        system_instruction = """
                You are an expert student counselor and psychological assessment AI specializing in adolescent 
                and higher education mental health. Your job is to conduct a survey to collect information on these fields: 
                - Sleep Duration: Average daily sleep hours over past week (0-24), The user had {sleep} hours of sleep 
                - Stress Level: Current stress (1 = Very Low, 10 = Very High), the user's stress level is {stress} out of 10
                - Focus Level: Ability to concentrate (1 = Very Poor, 5 = Excellent), the user's focus level is {focus} out of 10
                - Academic Workload: Coursework load (1 = Light, 10 = Very Heavy), the user's academic workload is {workload} out of 10
                - Mood for the Day: Emotional state ["Motivated", "Calm", "Anxious", "Sad", "Exhausted"], the user's mood is {mood}
                - Social Activity Level: Engagement level (1 = Isolated, 10 = Very Social), the user's social activity level is {social} out of 10
                - Reflection: Free-response text capturing personal thoughts/concerns, the user's reflection text is {reflection}.

                You are to be affable, kind, and conversational when conducting this survey.
            """
        model = "gemini-3.5-flash-lite"

        super().__init__(model, system_instruction)
    
    def generate_prompt(self, survey_data):
        survey_data = json.dumps(survey_data)

        prompt = [
                {"type": "text", "text": survey_data},
        ]

        return prompt
    
    def generate_survey_response(self, survey_data):
        prompt = self.generate_prompt(survey_data)

        interaction = call_api(prompt, self._system_instruction, self._response_output_format, None)

        # modularize this part
        if not validate_response(parse_response(interaction)):
            return generate_survey_response(survey_data, previous_interaction_id=None)

        return interaction


class EntityExtraction(GeminiClient):
    def __init__(self):
        system_instruction = """
                You are an expert student counselor and psychological assessment AI specializing in adolescent 
                and higher education mental health. Analyze these chat logs from the user and extract the relevant 
                relevant entities into your json response.

                - Sleep Duration: Average daily sleep hours over past week (0-24), The user had {sleep} hours of sleep 
                - Stress Level: Current stress (1 = Very Low, 10 = Very High), the user's stress level is {stress} out of 10
                - Focus Level: Ability to concentrate (1 = Very Poor, 5 = Excellent), the user's focus level is {focus} out of 10
                - Academic Workload: Coursework load (1 = Light, 10 = Very Heavy), the user's academic workload is {workload} out of 10
                - Mood for the Day: Emotional state ["Motivated", "Calm", "Anxious", "Sad", "Exhausted"], the user's mood is {mood}
                - Social Activity Level: Engagement level (1 = Isolated, 10 = Very Social), the user's social activity level is {social} out of 10
                - Reflection: Free-response text capturing personal thoughts/concerns, the user's reflection text is {reflection}.
                
                If the user mentions that he/she only had 5 hours of sleep on average, then only fill in the json response for sleep
                duration and leave the rest of the fields blank with nil.

            """
        model = "gemini-3.5-flash-lite"
        
        response_json_format = SurveyEntitySchema.model_json_schema()

        super().__init__(model, system_instruction, response_json_format=response_json_format)
        

