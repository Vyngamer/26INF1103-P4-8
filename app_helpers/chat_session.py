'''
One user's chatbot conversation
'''

import logging
import threading

from pydantic import ValidationError

from ai_manager import AIManager
from ai_manager_helper.data_classes.conversation import Conversation

_logger = logging.getLogger(__name__)


# One user's chat session
class ChatSession:
    GREETING = "Hello!"
    REPLY_TIMEOUT_SECONDS = 120
    FALLBACK_REPLY = "Sorry, I'm having trouble replying right now. Please try sending your message again."

    def __init__(self):
        self.__conversation = Conversation()
        self.__ai_manager = AIManager()
        self.__ai_manager.connect_client()
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
        self.__ai_manager.deny_survey()
        self.__reply_in_background(reason)

    # Asks the AI for the wellness assessment of validated survey answers
    # returns an APIResult
    def analyse(self, user_input):
        return self.__ai_manager.get_ai_output(user_input)

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
            response = self.__ai_manager.prompt_bot(prompt)
        except Exception:
            _logger.exception("Chatbot reply failed")
            response = {'text': self.FALLBACK_REPLY, 'survey_done': False}

        self.__conversation.add_message('ai', 'AI', response['text'])
        self.__conversation.set_bot_typing(False)
        self.__reply_ready.set()
        return response