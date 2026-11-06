"""
Common input prompt classes that ask repeatedly until receiving
standard valid answers
"""

import pwinput
import sys
from abc import ABC, abstractmethod


# Raised by Prompt.convert() / Prompt.validate() to reject an answer.
# Exception message is printed and the user is asked again.
class InvalidInput(ValueError):
    pass


# Abstract base class for every console prompt (Template Method pattern).
class Prompt(ABC):
    def __init__(self, message):
        self.message = message

    #Keep asking until the answer converts and validates, then return it
    def ask(self):
        while True:
            raw = self.read()
            try:
                value = self.convert(raw)
                self.validate(value)
            except InvalidInput as problem:
                print(problem)
                continue
            return value

    #Read one raw answer (whitespace trimmed)
    def read(self):
        return input(self.message).strip()

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

    def __init__(self, message, max_length=None, too_long_msg=None):
        super().__init__(message)
        self.max_length = max_length
        self.too_long_msg = too_long_msg or f"Please enter at most {max_length} characters."

    def convert(self, raw):
        if not raw:
            raise InvalidInput(self.EMPTY_MESSAGE)
        return raw

    # Check for maximum length if specified
    def validate(self, value):
        if self.max_length is not None and len(value) > self.max_length:
            raise InvalidInput(self.too_long_msg)


# Prompt for a password (input hidden). Raises InvalidInput if empty.
class PasswordPrompt(TextPrompt):
    EMPTY_MESSAGE = "Password cannot be empty. Please try again."

    def read(self):
        if sys.stdin.isatty():
            return pwinput.pwinput(prompt=self.message).strip()
        return input(self.message).strip()


# Number input with range validation.
class RangePrompt(Prompt):
    def __init__(self, message, minimum, maximum, cast=int):
        super().__init__(message)
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


# Shows a numbered list of options
# Returns the chosen option
# Inherits number parsing / range checking from RangePrompt
class ChoicePrompt(RangePrompt):
    def __init__(self, options, heading, message, footer=""):
        options = list(options)
        if not options:     # Rejects an empty list of options
            raise ValueError("ChoicePrompt needs at least one option.")
        super().__init__(message, 1, len(options))
        self.options = options
        self.heading = heading
        self.footer = footer

    def ask(self):
        print(self.heading)
        for i, option in enumerate(self.options, start=1):
            print(f"{i}. {option}")
        if self.footer:
            print(self.footer)
        return self.options[super().ask() - 1]


# Returns True for y/yes, False for n/no
class YesNoPrompt(Prompt):
    def convert(self, raw):
        answer = raw.lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        raise InvalidInput("Please enter y or n.")