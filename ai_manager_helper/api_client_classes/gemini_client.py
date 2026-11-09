from google import genai
import sys
import os
import json
import google
from google.genai._gaos.lib.compat_errors import APIConnectionError, NotFoundError
from ai_manager_helper.ai_error_handler import APIErrorHandler
from ai_manager_helper.data_classes.api_result import APIResult
from ai_manager_helper.data_classes.survey_entity_schema import SurveyEntitySchema

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
            return APIResult.ok(interaction.output_text)

        except Exception as e:
            return APIResult.fail(e)

