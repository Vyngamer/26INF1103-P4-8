from google import genai
from google.genai import types
from ai_manager_helper.interfaces.chat_client import IChatClient
from typing import Optional

class GeminiClient(IChatClient):
    def __init__(self, model: str, retry_config: types.HttpRetryOptions) -> None:
        self.__model = model
        self.__retry_config = retry_config
        self.__client = None

    def connect_client(self) -> None:
        self.__client = genai.Client(
            http_options=types.HttpOptions(
                retry_options=self.__retry_config,
                timeout=120*1000,
            )
        )

    def send_message(self, prompt: str, previous_interaction_id: str, system_instruction: Optional[str] = None, json_response_schema: Optional[dict] = None) -> dict:
        interaction = self.__client.interactions.create(
            model=self.__model,
            input=prompt,
            system_instruction=system_instruction,
            previous_interaction_id=previous_interaction_id,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": json_response_schema
            },
        )

        return interaction.model_dump()

