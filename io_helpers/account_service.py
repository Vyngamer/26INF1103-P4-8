'''
User Account Actions
'''

import functools
from io_helpers.hasher import PasswordHasher
from io_helpers.prompts import TextPrompt, PasswordPrompt
from io_helpers.account_models import AccountResult, AccountError
from io_helpers.validators import username_errors, password_errors, MIN_PASSWORD_LENGTH

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


# All account actions (was user_register / user_login / change_username / change_password).
class AccountService:
    def __init__(self, data, passwords=None):
        self.data = data
        self.passwords = passwords or PasswordHasher()

    # usernames stored & looked up in lowercase
    # e.g. "Alice" and "alice" get the same account
    @staticmethod
    def _ask_username(prompt):
        return TextPrompt(prompt).ask().lower()

    #Prompt for a username and reject it if invalid or already taken
    #Does not reject the user's own current name (so changing to it is harmless)
    def _prompt_unique_username(self, prompt, current_uid=None):
        username = self._ask_username(prompt)
        problems = username_errors(username)
        if problems:
            raise AccountError(" ".join(problems))
        existing = self.data.get_user_by_username(username)
        if existing is not None and existing.get_user_id() != current_uid:
            raise AccountError("Username already exists, please try again.")
        return username

    #Return the logged-in user (raises AccountError if not found)
    def _load_current_user(self, uid):
        user = self.data.get_user_by_id(uid)
        if user is None:
            raise AccountError("Current user not found.")
        return user

    #Ask for a new password twice and return it (was prompt_new_password)
    def _prompt_new_password(self, noun="Password"):
        print(f"Password must:\n1. Be at least {MIN_PASSWORD_LENGTH} characters long\n2. Contain at least one number & one special character (e.g. ! @ # $ %)\n(Spaces at the start or end are ignored)")
        password = PasswordPrompt(f"Please Enter A {noun}: ").ask()
        problems = password_errors(password)
        if problems:
            raise AccountError("Password must have: " + ", ".join(problems) + ".")
        confirm_password = PasswordPrompt(f"Please Re-enter The {noun}: ").ask()
        if password != confirm_password:
            raise AccountError("Passwords do not match, please try again.")
        return password

    #Register New User
    @account_action
    def register(self):
        print("Create a new user")
        username = self._prompt_unique_username("Please Enter A Username: ")
        password = self._prompt_new_password()

        uid = self.data.create_user(username, self.passwords.hash(password))
        if uid is None:
            raise AccountError("Could not create your account. Please try again.")
        return AccountResult(True, "Account created successfully!", uid=uid, username=username)

    #Login Existing User
    @account_action
    def login(self):
        if not self.data.get_users():
            raise AccountError("No users registered yet. Please register first.")

        username = self._ask_username("Please Enter Your Username: ")
        password = PasswordPrompt("Please Enter Your Password: ").ask()

        user = self.data.get_user_by_username(username)
        if user is None or not self.passwords.verify(password, user.get_password()):
            raise AccountError("Invalid username or password.")

        return AccountResult(True, f"Login successful! Welcome, {user.get_username()}!",
                             uid=user.get_user_id(), username=user.get_username())

    #Change Username
    @account_action
    def change_username(self, uid):
        self._load_current_user(uid)
        new_username = self._prompt_unique_username("Enter your new username: ", current_uid=uid)

        if not self.data.update_user(uid, {"username": new_username}):
            raise AccountError("Could not update your username. Please try again.")
        return AccountResult(True, "Username updated successfully!", username=new_username)

    #Change Password
    @account_action
    def change_password(self, uid):
        user = self._load_current_user(uid)

        current_password = PasswordPrompt("Please Enter Your Current Password: ").ask()
        if not self.passwords.verify(current_password, user.get_password()):
            raise AccountError("Incorrect current password. Please try again.")

        new_hash = self.passwords.hash(self._prompt_new_password("New Password"))
        if not self.data.update_user(uid, {"password": new_hash}):
            raise AccountError("Could not update your password. Please try again.")
        return AccountResult(True, "Password updated successfully!")
