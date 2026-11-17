'''
User account result
'''

from dataclasses import dataclass

# Returned from every account action
@dataclass
class AccountResult:
    ok: bool
    message: str
    uid: str = None
    username: str = None