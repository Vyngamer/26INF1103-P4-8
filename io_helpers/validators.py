'''
Username and password validation rules
'''

import re

MIN_PASSWORD_LENGTH = 4

# Each function returns a list of problems (empty list = valid).

USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9 _\-.]{3,20}$')
USERNAME_RULES = "Username must be 3-20 characters long and contain only letters, numbers, spaces, _, -, or ."

# Validates a username: 3-20 characters, letters/numbers/spaces/_/./-
def username_errors(value):
    return [] if USERNAME_PATTERN.match(value) else [USERNAME_RULES]

# Validates a password: >= 4 characters, >= 1 number, >= 1 special character
def password_errors(value, min_length=MIN_PASSWORD_LENGTH):
    problems = []

    # Check for minimum length
    if len(value) < min_length:
        problems.append(f"at least {min_length} characters")

    # Check for at least one number
    if not any(char.isdigit() for char in value):
        problems.append("at least one number")

    # Check for at least one special character
    if not any(not char.isalnum() and not char.isspace() for char in value):
        problems.append("at least one special character (e.g. ! @ # $ %)")

    return problems