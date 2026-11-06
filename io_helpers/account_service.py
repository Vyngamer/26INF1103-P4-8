'''
User Account Actions
'''

import functools
import uuid
from io_helpers.hasher import PasswordHasher
from io_helpers.prompts import TextPrompt, PasswordPrompt
from io_helpers.account_models import User, AccountResult, AccountError
from io_helpers.user_repository import UserRepository
from io_helpers.validators import UsernameValidator, PasswordValidator


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