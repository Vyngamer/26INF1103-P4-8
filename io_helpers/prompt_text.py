'''
Text Prompt (Child of Prompt)
'''

from io_helpers.prompts import Prompt
from io_helpers.errors.invalid_input import InvalidInput

# Non-empty text input (whitespace trimmed), with an optional maximum length
class TextPrompt(Prompt):
    EMPTY_MESSAGE = "Input cannot be empty. Please try again."

    def __init__(self, max_length=None, too_long_msg=None):
        self.max_length = max_length
        if max_length is not None and too_long_msg is None:
            too_long_msg = f"Please enter at most {max_length} characters."
        self.too_long_msg = too_long_msg

    def convert(self, raw):
        if not raw:
            raise InvalidInput(self.EMPTY_MESSAGE)
        return raw

    # Check for maximum length if specified
    def validate(self, value):
        if self.max_length is not None and len(value) > self.max_length:
            raise InvalidInput(self.too_long_msg)