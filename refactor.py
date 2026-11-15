from google import genai
from google.genai import types
from google.genai._gaos.lib.compat_errors import APIConnectionError, NotFoundError
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ai_manager_helper.data_classes.survey_entity_schema import SurveyEntitySchema
from ai_manager_helper.data_classes.conversation import Conversation

import re
import logging
import json

logger = logging.getLogger(__name__)


if __name__ == "__main__":

    retry_config = types.HttpRetryOptions(
        attempts=5,                         
        initial_delay=2.0,                  
        max_delay=60.0,                     
        http_status_codes=[408, 429, 500, 502, 503, 504],
    )     

    primary_client = GeminiClient('gemini-3.5-flash-lite', retry_config)
    primary_client.connect_client()
    fallback_client = GeminiClient('gemini-3.1-flash-lite', retry_config)
    client = GeminiClientWithFallback(primary_client, fallback_client)

    conversation = Conversation()
    ai_manager = AIManager(client, conversation)
    collect_survey_strategy = CounsellingStrategyFactory.create_strategy('survey')
    print(ai_manager.process_message('Hello!', collect_survey_strategy)['text'])
