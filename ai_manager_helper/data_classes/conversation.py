from dataclasses import dataclass
from typing import Literal


@dataclass
class Message:
    sender: Literal['user', 'ai']
    avatar: Literal['YT', 'AI']
    message: str

    def asdict(self):
        return self.__dict__


class Conversation:
    def __init__(self):
        self.__conversation_list = []
        self.__bot_typing = False
        self.__done = False

    def add_message(self, sender, avatar, message):
        self.__conversation_list.append(Message(sender, avatar, message))

    def set_bot_typing(self, status):
        if not isinstance(status, bool):
            raise ValueError("Status has to be a boolean.")

        self.__bot_typing = status

    def is_bot_typing(self):
        return self.__bot_typing

    def logs(self):
        conversation_list = [msg.asdict() for msg in self.__conversation_list]
        return conversation_list

    def get_last_log(self):
        return self.__conversation_list[-1].asdict()

    def is_done(self):
        return self.__done

    def set_done(self, done):
        self.__done = done

    def reset_conversation(self):
        self.__conversation_list = []


if __name__ == "__main__":
    conversation = Conversation()
    conversation.add_message('user', 'asdf')
    conversation.add_message('ai', 'Hello')
    print(conversation.logs())
