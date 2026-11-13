'''
User Account Error
'''

# Raised inside AccountService to stop an action early with a message.
# Turned into a failed AccountResult before reaching the caller.
class AccountError(Exception):
    pass