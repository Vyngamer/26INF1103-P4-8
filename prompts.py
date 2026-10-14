"""
Common input functions to ask repeatedly until receiving
standard valid answers
"""

import pwinput
import sys


#Non-empty text input (whitespace trimmed)
def prompt_text(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Input cannot be empty. Please try again.")

#Non-empty hidden input. Passwords are NOT stripped so that
#register / login / change-password all treat them the same way
def prompt_password(prompt):
    while True:
        if sys.stdin.isatty():
            value = pwinput.pwinput(prompt=prompt)
        else:
            value = input(prompt)
        if value:
            return value
        print("Password cannot be empty. Please try again.")

#Number input with range validation. cast=int for whole numbers, cast=float for decimals
def prompt_range(prompt, minimum, maximum, cast=int):
    error = "Please enter a whole number." if cast is int else "Please enter a valid number."
    while True:
        try:
            value = cast(input(prompt).strip())
        except ValueError:
            print(error)
            continue
        if minimum <= value <= maximum:
            return value
        print(f"Please enter a number from {minimum} to {maximum}.")

#Show a numbered list of options and return the chosen option (the item itself, not its number)
def prompt_choice(options, heading, prompt, footer=""):
    print(heading)
    for i, option in enumerate(options, start=1):
        print(f"{i}. {option}")
    if footer:
        print(footer)
    choice = prompt_range(prompt, 1, len(options))
    return options[choice - 1]

#Yes/no question. Returns True for y/yes, False for n/no
def prompt_yes_no(prompt):
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please enter y or n.")