'''
User storage (users.json)
'''

import json
import os
from io_helpers.account_models import User, CorruptDatabaseError

DATABASE = "users.json"


# users.json file access (originally load_users / save_users / find_user / find_user_by_id)
class UserRepository:
    def __init__(self, path=DATABASE):
        self.path = path

    #Load users list. [] if the file doesn't exist yet. Raises CorruptDatabaseError if corrupted
    def load(self):
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                return [User.from_dict(data) for data in json.load(file)]
        except (json.JSONDecodeError, TypeError, KeyError):
            raise CorruptDatabaseError()

    #Save users list (write to a temp file first for program crash handling)
    def save(self, users):
        temp_file = self.path + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump([user.to_dict() for user in users], file, indent=4)
        os.replace(temp_file, self.path)

    #Find a user by username, case-insensitive (None if not found)
    @staticmethod
    def find_by_username(users, username):
        for user in users:
            if user.username.lower() == username.lower():
                return user
        return None

    #Find a user by id (None if not found)
    @staticmethod
    def find_by_id(users, uid):
        for user in users:
            if user.user_id == uid:
                return user
        return None