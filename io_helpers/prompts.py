"""
Common answer checks: each takes one answer (passed in as a parameter)
and returns it converted to the right type, or rejects it with a message
"""

from abc import ABC, abstractmethod


# Raised by Prompt.convert() / Prompt.validate() to reject an answer.
class InvalidInput(ValueError):
    pass


# abstract base class for every answer check
class Prompt(ABC):

    # Returns the converted answer, or raises InvalidInput with the reason
    def parse(self, raw):
        value = self.convert(self.clean(raw))
        self.validate(value)
        return value

    # Turns the given answer into text with whitespace trimmed
    # None (e.g. a missing form field) counts as empty
    @staticmethod
    def clean(raw):
        return "" if raw is None else str(raw).strip()

    #Turn the raw text into the answer's type. Raise InvalidInput to reject it
    @abstractmethod
    def convert(self, raw):
        pass

    #Extra checks on the converted value. Raise InvalidInput to reject it
    def validate(self, value):
        pass


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


# One answer from a list of options
# Returns the chosen option
# Inherits number parsing / range checking from RangePrompt
class ChoicePrompt(RangePrompt):
    def __init__(self, options):
        options = list(options)
        if not options:     # Rejects an empty list of options
            raise ValueError("ChoicePrompt needs at least one option.")
        super().__init__(1, len(options))
        self.options = options
        # Msg for an answer that is neither one of the options nor its number
        self.choose_msg = "Please choose one of: " + ", ".join(str(option) for option in options) + "."

    # Accepts the option itself in any letter case (e.g. "calm" from chatbot)
    # or its number (1 = first option). Returns the option as written in options
    def parse(self, raw):
        text = self.clean(raw)
        for option in self.options:
            if text.lower() == str(option).lower():
                return option
        try:
            return self.options[super().parse(text) - 1]
        except InvalidInput:
            raise InvalidInput(self.choose_msg) from None