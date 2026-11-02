from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Any
from google import genai
from io_manager import print_error, print_notice
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
                    "schema": self._response_output_format
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
    def __init__(self, model, system_instruction, response_json_format):

        # missing parameters
        super().__init__(model, system_instruction, response_json_format)
    
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

