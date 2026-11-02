from dataclass import dataclass
from typing import Generic, TypeVar, Optional, Any
from google import genai
from io_manager import print_error, print_notice
import sys
import os
import json
import google
from google.genai._gaos.lib.compat_errors import APIConnectionError, NotFoundError


@dataclass(frozen=True)
class APIResult(Generic[TypeVar('T'), TypeVar('E')]):
    success: bool
    data: Optional[T] = None
    error: Optional[E] = None

    @classmethod
    def ok(cls, data):
        return cls(success=True, data=data)

    def fail(cls, error):
        return cls(success=False, error=error)

@dataclass
class GeminiErrorDetails:
    message: str
    code: Optional[str] = None
    exception_type: str = "UnknownException"


class GeminiClient:
    def __init__(self, model, system_instruction, response_json_format):
        self._model = model
        self._system_instruction = system_instruction
        self._response_json_format = response_json_format
        self._client = None
    
    def connect_client():
        self._client = genai.Client()

    def call_api(self, prompt, system_instruction, previous_interaction_id, response_output_format):
        interaction = self.__client.interactions.create(
            model=self._model,
            input=prompt,
            system_instruction=system_instruction,
            previous_interaction_id=previous_interaction_id,
            response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": response_output_format
        })

        return interaction

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
