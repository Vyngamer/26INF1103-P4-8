'''
Username and password validation rules
'''

import re
from abc import ABC, abstractmethod

MIN_PASSWORD_LENGTH = 4


# Abstract base class for input rules. errors() returns a list of problems (empty list = valid).
class Validator(ABC):
    @abstractmethod
    def errors(self, value):
        pass


# Validates a username: 3-20 characters, letters/numbers/spaces/_/./-
class UsernameValidator(Validator):
    PATTERN = re.compile(r'^[a-zA-Z0-9 _\-.]{3,20}$')
    RULES = "Username must be 3-20 characters long and contain only letters, numbers, spaces, _, -, or ."

    def errors(self, value):
        return [] if self.PATTERN.match(value) else [self.RULES]


# Validates a password: >= 4 characters, >= 1 number, >= 1 special character, no spaces at start or end
class PasswordValidator(Validator):
    def __init__(self, min_length=MIN_PASSWORD_LENGTH):
        self.min_length = min_length

    def errors(self, value):
        problems = []

        # Check for minimum length
        if len(value) < self.min_length:
            problems.append(f"at least {self.min_length} characters")

        # Check for no spaces
        if value != value.strip():
            problems.append("no spaces at the start or end")

        # Check for at least one number
        if not any(char.isdigit() for char in value):
            problems.append("at least one number")

        # Check for at least one special character
        if not any(not char.isalnum() and not char.isspace() for char in value):
            problems.append("at least one special character (e.g. ! @ # $ %)")

        return problems