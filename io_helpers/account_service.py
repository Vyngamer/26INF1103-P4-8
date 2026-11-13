'''
User Account Actions
'''

import functools
from hasher import PasswordHasher
from io_helpers.account_result import AccountResult
from errors.account_error import AccountError
from validators import username_errors, password_errors

# Decorator for AccountService actions
# Wraps the method so any AccountError raised inside it becomes a failed AccountResult.
def account_action(method):
    @functools.wraps(method)    # Keep the original method's name and docstring
    def wrapper(self, *args, **kwargs):   # **kwargs so callers can pass answers by name
        try:
            return method(self, *args, **kwargs)
        except AccountError as error:
            return AccountResult(False, str(error))
    return wrapper


# All account actions (was user_register / user_login / change_username / change_password).
# Each action takes the user's answers as parameters (from the web app's forms)
class AccountService:
    def __init__(self, data, passwords=None):
        self.data = data
        self.passwords = passwords or PasswordHasher()

    # One answer as text with whitespace trimmed
    # None (e.g. a missing form field) counts as empty
    @staticmethod
    def _clean(value):
        return "" if value is None else str(value).strip()

    # usernames stored in lowercase
    # e.g. "Alice" and "alice" get the same account
    @classmethod
    def _clean_username(cls, username):
        return cls._clean(username).lower()

    # Find account with username (case-insensitive)
    def _find_user(self, username):
        users = self.data.get_users()
        for wanted in (username, username.lower()):
            for user in users:
                if user.get_username() == wanted:
                    return user
        for user in users:
            if user.get_username().lower() == username.lower():
                return user
        return None

    # Check if a username already exists
    def _username_taken(self, username, current_uid=None):
        return any(user.get_username().lower() == username.lower() and user.get_user_id() != current_uid
                   for user in self.data.get_users())

    # Reject a username if invalid or already taken
    # Does not reject the user's own current name (so changing to it is harmless)
    def _check_unique_username(self, username, current_uid=None):
        problems = username_errors(username)
        if problems:
            raise AccountError(" ".join(problems))
        if self._username_taken(username, current_uid):
            raise AccountError("This username already exists. Please choose another.")
        return username

    #Return the logged-in user (raises AccountError if not found)
    def _load_current_user(self, uid):
        user = self.data.get_user_by_id(uid)
        if user is None:
            raise AccountError("Current user not found.")
        return user

    # Checks a given password against the rules, each action checks the confirmation itself
    @staticmethod
    def _check_password_rules(password):
        problems = password_errors(password)
        if problems:
            raise AccountError("Password must have " + ", ".join(problems) + ".")

    # Register New User
    @account_action
    def register(self, username, password, confirm):
        username = self._check_unique_username(self._clean_username(username))
        password = self._clean(password)
        self._check_password_rules(password)
        if password != self._clean(confirm):
            raise AccountError("Passwords do not match.")

        try:
            uid = self.data.create_user(username, self.passwords.hash(password))
        except (ConnectionError, ValueError):
            raise AccountError("Unable to connect to the database. Please try again later.")
        if uid is None:
            raise AccountError("Could not create your account. Please try again.")
        return AccountResult(True, "Account created successfully!", uid=uid, username=username)

    # Login Existing User
    @account_action
    def login(self, username, password):
        if not self.data.get_users():
            raise AccountError("No users registered yet. Please register first.")

        user = self._find_user(self._clean(username))
        if user is None or not self.passwords.verify(self._clean(password), user.get_password()):
            raise AccountError("Invalid username or password.")

        return AccountResult(True, f"Login successful! Welcome, {user.get_username()}!",
                             uid=user.get_user_id(), username=user.get_username())

    # Change Username
    @account_action
    def change_username(self, uid, new_username):
        self._load_current_user(uid)
        new_username = self._clean_username(new_username)
        if not new_username:
            raise AccountError("Please Enter a username")
        self._check_unique_username(new_username, current_uid=uid)

        if not self.data.update_user(uid, {"username": new_username}):
            raise AccountError("There was an error with updating your username. Please try again.")
        return AccountResult(True, "Your username has been successfully updated!", username=new_username)

    # Change Password
    @account_action
    def change_password(self, uid, current_password, new_password, confirm):
        user = self._load_current_user(uid)

        current_password = self._clean(current_password)
        if not current_password:
            raise AccountError("Please enter your old password")
        if not self.passwords.verify(current_password, user.get_password()):
            raise AccountError("Incorrect password. Please try again.")

        new_password = self._clean(new_password)
        if not new_password:
            raise AccountError("Please enter your new password")
        self._check_password_rules(new_password)
        confirm = self._clean(confirm)
        if not confirm:
            raise AccountError("Please confirm your new password")
        if new_password != confirm:
            raise AccountError("Your new password & confirmation do not match.")

        new_hash = self.passwords.hash(new_password)
        if not self.data.update_user(uid, {"password": new_hash}):
            raise AccountError("There has been an issue with updating your password. Please try again later")
        return AccountResult(True, "Your password has been successfully updated!")

    # Get username by user id, or None if there is no such user
    def get_username(self, uid):
        user = self.data.get_user_by_id(uid)
        return None if user is None else user.get_username()