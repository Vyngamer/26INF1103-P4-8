import logging

from ai_manager_helper.interfaces.chat_client import IChatClient
from google.genai._gaos.lib.compat_errors import APIConnectionError, NotFoundError
from typing import Optional

logger = logging.getLogger(__name__)

class GeminiClientWithFallback(IChatClient):
    def __init__(self, primary_model: IChatClient, fallback_model: IChatClient) -> None:
        self.__primary = primary_model
        self.__fallback = fallback_model

    def send_message(self, prompt: str, previous_interaction_id: str, system_instruction: Optional[str] = None, json_response_schema: Optional[dict] = None):
        try:
            return self.__primary.send_message(prompt, previous_interaction_id, system_instruction, json_response_schema)

        except (APIConnectionError, NotFoundError) as e:
            logger.warning(
                f"Primary AI model failed with error: {str(e)}. "
                "Switching to fallback model..."
            )

            try: 
                self.__fallback.connect_client()
                return self.__fallback.send_message(prompt, previous_interaction_id, system_instruction, json_response_schema)
                
            except Exception as e:
                logger.error(f"Fallback AI model also failed: {str(e)}")
                raise Exception("All AI counselling services are currently unavailable.")

