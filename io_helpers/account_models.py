'''
User account data classes and errors
'''

from dataclasses import dataclass


# One user account
@dataclass
class User:
    user_id: str
    username: str
    password: str     #hashed password

    @classmethod
    def from_dict(cls, data):
        return cls(data["user_id"], data["username"], data["password"])

    def to_dict(self):
        return {"user_id": self.user_id, "username": self.username, "password": self.password}


# Originally make_result(). Returned from every account action
@dataclass
class AccountResult:
    ok: bool
    message: str
    uid: str = None
    username: str = None


# Raised inside AccountService to stop an action early with a message.
# Turned into a failed AccountResult before reaching the caller.
class AccountError(Exception):
    pass