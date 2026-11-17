'''
Chat sessions of logged-in users
'''

import threading

from app_helpers.ChatSession import ChatSession


# Keeps one ChatSession per user id
class ChatRegistry:

    def __init__(self, session_factory=ChatSession):
        self.__session_factory = session_factory
        self.__sessions = {}
        self.__lock = threading.Lock()    # Flask serves requests on several threads

    # The user's chat, created the first time they need one
    def get(self, uid):
        with self.__lock:
            if uid not in self.__sessions:
                self.__sessions[uid] = self.__session_factory()
            return self.__sessions[uid]

    # Ends the user's chat
    # Next get() starts a fresh one
    def discard(self, uid):
        with self.__lock:
            self.__sessions.pop(uid, None)