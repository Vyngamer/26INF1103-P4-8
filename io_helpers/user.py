'''
User Account Actions
'''

import functools
import json
import os
import uuid
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from io_helpers.hasher import PasswordHasher
from io_helpers.prompts import TextPrompt, PasswordPrompt

DATABASE = "users.json"
MIN_PASSWORD_LENGTH = 4

'''
Data classes
'''

# One user account
@dataclass
class User:
    user_id: str
    username: str
    password: str     #hashed password

    @classmethod
    def from_dict(cls, data):
        return cls(data["user_id"], data["username"], data["password"])

    def to_dict(self):
        return {"user_id": self.user_id, "username": self.username, "password": self.password}


# Originally make_result(). Returned from every account action
@dataclass
class AccountResult:
    ok: bool
    message: str
    uid: str = None
    username: str = None


# Raised inside AccountService to stop an action early with a message.
# Turned into a failed AccountResult before reaching the caller.
class AccountError(Exception):
    pass


# Raised when users.json cannot be parsed
class CorruptDatabaseError(AccountError):
    def __init__(self):
        super().__init__("User database is corrupted. Please check users.json.")


# Decorator for AccountService actions
# Wraps the method so any AccountError raised inside it becomes a failed AccountResult.
def account_action(method):
    @functools.wraps(method)    # keep the original method's name and docstring
    def wrapper(self, *args):
        try:
            return method(self, *args)
        except AccountError as error:
            return AccountResult(False, str(error))
    return wrapper


'''
Storage
'''

# users.json file access (originally load_users / save_users / find_user / find_user_by_id)
class UserRepository:
    def __init__(self, path=DATABASE):
        self.path = path

    #Load users list. [] if the file doesn't exist yet. Raises CorruptDatabaseError if corrupted
    def load(self):
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                return [User.from_dict(data) for data in json.load(file)]
        except (json.JSONDecodeError, TypeError, KeyError):
            raise CorruptDatabaseError()

    #Save users list (write to a temp file first for program crash handling)
    def save(self, users):
        temp_file = self.path + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump([user.to_dict() for user in users], file, indent=4)
        os.replace(temp_file, self.path)

    #Find a user by username, case-insensitive (None if not found)
    @staticmethod
    def find_by_username(users, username):
        for user in users:
            if user.username.lower() == username.lower():
                return user
        return None

    #Find a user by id (None if not found)
    @staticmethod
    def find_by_id(users, uid):
        for user in users:
            if user.user_id == uid:
                return user
        return None


'''
Validation
'''

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


'''
User Actions
'''

# All account actions (was user_register / user_login / change_username / change_password). 
class AccountService:
    def __init__(self, repository=None, passwords=None,
                 username_rules=None, password_rules=None):
        self.repository = repository or UserRepository()
        self.passwords = passwords or PasswordHasher()
        self.username_rules = username_rules or UsernameValidator()
        self.password_rules = password_rules or PasswordValidator()

    #Prompt for a username and reject it if invalid or already taken
    #Does not check if user's own name is taken, allowing them to change their own username 
    #To the same name in diff case (e.g. "Alice" -> "alice")
    def _prompt_unique_username(self, users, prompt, current=None):
        username = TextPrompt(prompt).ask()
        problems = self.username_rules.errors(username)
        if problems:
            raise AccountError(" ".join(problems))
        existing = self.repository.find_by_username(users, username)
        if existing is not None and existing is not current:
            raise AccountError("Username already exists, please try again.")
        return username

    #Load the users list and the logged-in user (raises AccountError if not found)
    def _load_current_user(self, uid):
        users = self.repository.load()
        user = self.repository.find_by_id(users, uid)
        if user is None:
            raise AccountError("Current user not found.")
        return users, user

    #Ask for a new password twice and return it (was prompt_new_password)
    def _prompt_new_password(self, noun="Password"):
        print(f"Password must:\n1. Be at least {self.password_rules.min_length} characters long\n2. Contain at least one number & one special character (e.g. ! @ # $ %)\n3. Have no spaces at the start or end")
        password = PasswordPrompt(f"Please Enter A {noun}: ").ask()
        problems = self.password_rules.errors(password)
        if problems:
            raise AccountError("Password must have: " + ", ".join(problems) + ".")
        confirm_password = PasswordPrompt(f"Please Re-enter The {noun}: ").ask()
        if password != confirm_password:
            raise AccountError("Passwords do not match, please try again.")
        return password

    #Register New User
    @account_action
    def register(self):
        users = self.repository.load()
        print("Create a new user")
        username = self._prompt_unique_username(users, "Please Enter A Username: ")
        password = self._prompt_new_password()

        new_user = User(str(uuid.uuid4()), username, self.passwords.hash(password))
        users.append(new_user)
        self.repository.save(users)
        return AccountResult(True, "Account created successfully!",
                             uid=new_user.user_id, username=username)

    #Login Existing User
    @account_action
    def login(self):
        users = self.repository.load()
        if not users:
            raise AccountError("No users registered yet. Please register first.")

        username = TextPrompt("Please Enter Your Username: ").ask()
        password = PasswordPrompt("Please Enter Your Password: ").ask()

        user = self.repository.find_by_username(users, username)
        if user is None or not self.passwords.verify(password, user.password):
            raise AccountError("Invalid username or password.")

        return AccountResult(True, f"Login successful! Welcome, {user.username}!",
                             uid=user.user_id, username=user.username)

    #Change Username
    @account_action
    def change_username(self, uid):
        users, user = self._load_current_user(uid)
        new_username = self._prompt_unique_username(users, "Enter your new username: ", current=user)

        user.username = new_username
        self.repository.save(users)
        return AccountResult(True, "Username updated successfully!", username=new_username)

    #Change Password
    @account_action
    def change_password(self, uid):
        users, user = self._load_current_user(uid)

        current_password = PasswordPrompt("Please Enter Your Current Password: ").ask()
        if not self.passwords.verify(current_password, user.password):
            raise AccountError("Incorrect current password. Please try again.")

        user.password = self.passwords.hash(self._prompt_new_password("New Password"))
        self.repository.save(users)
        return AccountResult(True, "Password updated successfully!")