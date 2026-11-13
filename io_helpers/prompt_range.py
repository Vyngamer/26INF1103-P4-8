'''
Range Prompt (Child of Prompt)
'''

from io_helpers.prompts import Prompt
from io_helpers.errors.invalid_input import InvalidInput

# Number input with range validation.
class RangePrompt(Prompt):
    def __init__(self, minimum, maximum, cast=int):
        self.minimum = minimum
        self.maximum = maximum
        self.cast = cast    # cast=int for whole numbers, cast=float for decimals

    def convert(self, raw):
        try:
            return self.cast(raw)
        except ValueError:
            raise InvalidInput("Please enter a whole number." if self.cast is int
                               else "Please enter a valid number.")

    def validate(self, value):
        if not self.minimum <= value <= self.maximum:
            raise InvalidInput(f"Please enter a number from {self.minimum} to {self.maximum}.")