'''
One user's chatbot conversation
'''

import logging
import threading
import json

from pydantic import ValidationError
from google.genai import types

from ai_manager import AIManager
from ai_manager_helper.data_classes.conversation import Conversation
from ai_manager_helper.crisis_safety_filter import CrisisSafetyFilter
from ai_manager_helper.crisis_safety_filter import CrisisDetectedError
from ai_manager_helper.gemini_client import GeminiClient
from ai_manager_helper.gemini_client_with_fallback import GeminiClientWithFallback
from ai_manager_helper.counselling_strategy_factory import CounsellingStrategyFactory

_logger = logging.getLogger(__name__)


# One user's chat session
class ChatSession:
    GREETING = "Hello!"
    REPLY_TIMEOUT_SECONDS = 120
    FALLBACK_REPLY = "Sorry, I'm having trouble replying right now. Please try sending your message again."

    def __init__(self):
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

        counselling_strategy_factory = CounsellingStrategyFactory()
        self.__collect_survey_strategy = counselling_strategy_factory.create_strategy('survey')
        self.__evaluate_survey_strategy = counselling_strategy_factory.create_strategy('evaluate')
        self.__conversation = Conversation()
        self.__ai_manager = AIManager(client=client, safety_filter=CrisisSafetyFilter())
        self.__reply_ready = threading.Event()
        self.__reply_ready.set()    # No reply is pending yet

    # Read-only access for wellness-check template
    @property
    def conversation(self):
        return self.__conversation

    # Greets user (in the background) the first time the chat page is opened
    def start(self):
        if not self.__conversation.logs() and not self.__conversation.is_bot_typing():
            self.__reply_in_background(self.GREETING)

    # Adds user's message and waits for chatbot's reply
    # Returns {'text': ..., 'survey_done': ...} for the page's script
    def send(self, message):
        self.__conversation.add_message('user', 'YT', message)
        self.__begin_reply()
        return self.__reply(message)

    # Waits for a reply started in the background, then returns newest message
    def wait_for_reply(self):
        self.__reply_ready.wait(self.REPLY_TIMEOUT_SECONDS)
        logs = self.__conversation.logs()
        return logs[-1] if logs else {'sender': 'ai', 'avatar': 'AI', 'message': self.FALLBACK_REPLY}

    # Survey answers collected by the chatbot so far, or None if it has none yet or they don't fit the chatbot's schema
    def survey_answers(self, by_alias=False):
        try:
            return dict(self.__ai_manager.show_survey_results(by_alias=by_alias))
        except (TypeError, ValidationError):
            return None

    # Tells chatbot that the survey answers are wrong, then lets it ask what to fix
    def deny_survey(self, reason):
        self.__ai_manager.process_message('The survey results are inaccurate: ' + \
                                           json.dumps(self.__ai_manager.show_survey_results()), self.__collect_survey_strategy)
        self.__reply_in_background(reason)

    # Asks the AI for the wellness assessment of validated survey answers
    # returns an APIResult
    def analyse(self, user_input):
        user_input = json.dumps(user_input)
        output = self.__ai_manager.process_message(user_input, self.__evaluate_survey_strategy)
        return output['text']

    # Shows a message from the app in the chat
    def notify(self, message):
        self.__conversation.add_message('ai', 'AI', message)

    def __begin_reply(self):
        self.__reply_ready.clear()
        self.__conversation.set_bot_typing(True)

    def __reply_in_background(self, prompt):
        self.__begin_reply()
        threading.Thread(target=self.__reply, args=(prompt,), daemon=True).start()

    # Gets the chatbot's reply and adds it to the conversation
    # Always clears typing state, so the page doesn't hang
    def __reply(self, prompt):
        try:
            response = self.__ai_manager.process_message(prompt, self.__collect_survey_strategy)
        except CrisisDetectedError:
            raise 
        except Exception:
            _logger.exception("Chatbot reply failed")
            response = {'text': self.FALLBACK_REPLY, 'survey_done': False}

        self.__conversation.add_message('ai', 'AI', response['text'])
        self.__conversation.set_bot_typing(False)
        self.__reply_ready.set()
        return response