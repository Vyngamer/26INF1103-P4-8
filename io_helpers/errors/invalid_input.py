'''
Invalid Input Error for Prompts
'''

# Raised by Prompt.convert() / Prompt.validate() to reject an answer.
class InvalidInput(ValueError):
    pass