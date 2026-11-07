'''
User account results and errors
'''

from dataclasses import dataclass

# Returned from every account action
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