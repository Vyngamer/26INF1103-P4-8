from dataclass import dataclass
from typing import Generic, TypeVar, Optional, Any
from google import genai
from io_manager import print_error, print_notice
import sys
import os
import json
import google
from google.genai._gaos.lib.compat_errors import APIConnectionError, NotFoundError


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
