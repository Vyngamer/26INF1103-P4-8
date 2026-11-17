"""
Abstract base class for all prompt classes
each child class will take one answer (passed in as a parameter)
and return it converted to the right type, or reject it with a message
"""

from abc import ABC, abstractmethod


# Abstract base class for every answer check
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