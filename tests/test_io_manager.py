"""
IO Manager Pytest Script
Run with:  python -m pytest tests/test_io_manager_oop.py -v
"""
from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path
from typing import Any, Iterable, Protocol
from unittest.mock import MagicMock

import pytest
from flask import Flask
from flask_mail import Mail

from IOManager import IOManager
from io_helpers.AccountService import AccountService
from data_manager_helper.UserRecord import UserRecord
from data_manager_helper.PasswordHasher import PasswordHasher
from io_helpers.validators import username_errors, password_errors, USERNAME_RULES
from io_helpers.TextPrompt import TextPrompt
from io_helpers.RangePrompt import RangePrompt
from io_helpers.ChoicePrompt import ChoicePrompt
from io_helpers.errors.InvalidInput import InvalidInput
from io_helpers.SurveyResponse import SurveyResponse
from io_helpers.SurveyResult import SurveyResult
from io_helpers.Questionnaire import Questionnaire, SurveyAnswersError


'''
Test data (one place for shared values and expected messages)
'''

# Shared sample objects and constants
class SampleData:

    # Sample completed survey, used by the survey tests
    RESPONSE = SurveyResponse("123", 7.5, 5, 6, 4, "Calm", 3, "Good week")

    # RESPONSE's answers without the user id, as the web app passes them to survey()
    ANSWERS = {key: value for key, value in RESPONSE.to_dict().items() if key != "user_id"}

    SCALE_KEYS = ("stress_level", "focus_level", "academic_workload", "social_activity_level")

    # Low iteration count so password hashing stays fast in tests
    FAST_HASH_ITERATIONS = 1000


# User-facing messages that several tests expect
class Messages:

    PASSWORD_RULES_ALL = ("Password must have at least 4 characters, at least one number, "
                          "at least one special character (e.g. ! @ # $ %).")
    MOOD_CHOICES = "Please choose one of: Motivated, Calm, Anxious, Sad, Exhausted."
    WHOLE_NUMBER = "Please enter a whole number."
    RANGE_1_TO_10 = "Please enter a number from 1 to 10."
    RANGE_0_TO_24 = "Please enter a number from 0 to 24."
    USERNAME_TAKEN = "This username already exists. Please choose another."


# Parameter tables for the survey boundary tests (extend here, not in the tests)
class SurveyLimitCases:

    # (question key, answer given as text, value expected after parsing)
    ACCEPTED = (
        [("sleep_duration", "0", 0), ("sleep_duration", "24", 24)]
        + [(key, answer, int(answer)) for key in SampleData.SCALE_KEYS for answer in ("1", "10")]
        + [("mood", "1", "Motivated"), ("mood", "5", "Exhausted")]
    )

    # (question key, answer just past a limit, that question's usual message)
    REJECTED = (
        [("sleep_duration", "-0.5", Messages.RANGE_0_TO_24),
         ("sleep_duration", "24.5", Messages.RANGE_0_TO_24)]
        + [(key, answer, Messages.RANGE_1_TO_10) for key in SampleData.SCALE_KEYS for answer in ("0", "11")]
        + [("mood", "0", Messages.MOOD_CHOICES), ("mood", "6", Messages.MOOD_CHOICES)]
    )


'''
Small interfaces (ISP) - structural, so the fakes need no inheritance
'''

# All a rejection check needs from a prompt
class Parser(Protocol):
    def parse(self, raw: Any) -> Any: ...


# Read side of the user data
class UserReader(Protocol):
    def get_users(self) -> list: ...
    def get_user_by_id(self, user_id: str) -> Any: ...


# Write side of the user data
class UserWriter(Protocol):
    def create_user(self, username: str, password: str) -> Any: ...
    def update_user(self, user_id: str, updates: dict) -> bool: ...
    def delete_user(self, user_id: str) -> bool: ...



class UserDataPort(UserReader, UserWriter, Protocol):
    """What AccountService needs from DataManager: reading and writing users."""


'''
Test doubles, builders and factories
'''


# Stand-in for DataManager's user methods, behaving like UserManager + MongoDBStorage
class FakeUserData:

    def __init__(self) -> None:
        self.users: list = []
        self.fail_saves = False    # set True to act like a MongoDB error

    def get_users(self) -> list:
        return self.users.copy()

    def get_user_by_id(self, user_id):
        return next((u for u in self.users if u.get_user_id() == user_id), None)

    def _taken(self, username, uid=None) -> bool:
        return any(u.get_username() == username and u.get_user_id() != uid for u in self.users)

    def create_user(self, username, password):
        if self.fail_saves or self._taken(username):
            return None
        user = UserRecord(username, password)
        self.users.append(user)
        return user.get_user_id()

    def update_user(self, user_id, updates) -> bool:
        user = self.get_user_by_id(user_id)
        if self.fail_saves or ("username" in updates and self._taken(updates["username"], user_id)):
            return False
        data = {**user.to_dict(), **updates}
        self.users[self.users.index(user)] = UserRecord(data["username"], data["password"], user_id)
        return True

    def delete_user(self, user_id) -> bool:
        user = self.get_user_by_id(user_id)
        if self.fail_saves or user is None:
            return False
        self.users.remove(user)
        return True


# Builds an AccountService from injected collaborators (defaults: fake data, fast hasher)
class AccountServiceFactory:

    def __init__(self, data: UserDataPort | None = None, hasher: PasswordHasher | None = None) -> None:
        self._data = data if data is not None else FakeUserData()
        self._hasher = hasher if hasher is not None else PasswordHasher(iterations=SampleData.FAST_HASH_ITERATIONS)

    def create(self) -> AccountService:
        return AccountService(self._data, self._hasher)


"""
Builds a fake assessment with the common values used by the email tests.
Subclass and override _user_input() / _ai_output() to change the values (open for extension).
"""
class AssessmentBuilder:

    DEFAULT_ROUTE = "Urgent support"

    def __init__(self) -> None:
        self._route = self.DEFAULT_ROUTE

    def with_route(self, route: str) -> AssessmentBuilder:
        self._route = route
        return self

    def build(self) -> MagicMock:
        assessment = MagicMock()
        assessment.get_logic_output.return_value = {"route": self._route}
        assessment.get_user_input.return_value = self._user_input()
        assessment.get_ai_output.return_value = self._ai_output()
        return assessment

    def _user_input(self) -> dict:
        return {
            "sleep_duration": 7.5, "stress_level": 5, "focus_level": 6,
            "academic_workload": 4, "mood": "Calm", "social_activity_level": 3,
            "reflection": "Good week",
        }

    def _ai_output(self) -> dict:
        return {
            "mental_wellness_risk_score": 2, "burnout_risk_score": 3,
            "personalized_recommendations": "Keep taking breaks.",
        }


# Context manager giving the email tests a Flask app context with Flask-Mail configured
class FlaskMailContext:

    def __init__(self, sender: str = "noreply@example.com") -> None:
        self._sender = sender
        self._context = None

    def __enter__(self) -> Flask:
        app = Flask(__name__)
        app.config["MAIL_DEFAULT_SENDER"] = self._sender
        Mail(app)
        self._context = app.app_context()
        self._context.__enter__()
        return app

    def __exit__(self, exc_type, exc, traceback):
        return self._context.__exit__(exc_type, exc, traceback)


# Finds the source files that make up the I/O layer
class ProjectSourceLocator:

    def __init__(self, root: Path, entry_file: str = "IOManager.py", helpers_dir: str = "io_helpers") -> None:
        self._root = root
        self._entry_file = entry_file
        self._helpers_dir = helpers_dir

    def files(self) -> list[Path]:
        return [self._root / self._entry_file, *sorted((self._root / self._helpers_dir).rglob("*.py"))]


# Reports calls to forbidden built-ins (default: input and print) in Python source files
class ForbiddenCallScanner:

    def __init__(self, forbidden: Iterable[str] = ("input", "print")) -> None:
        self._forbidden = frozenset(forbidden)

    def find(self, paths: Iterable[Path]) -> list[str]:
        return [f"{path.name}:{node.lineno} {node.func.id}()"
                for path in paths
                for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
                if self._is_forbidden_call(node)]

    def _is_forbidden_call(self, node: ast.AST) -> bool:
        return (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in self._forbidden)


'''
Shared test base classes (fixtures and helpers only - no tests)
'''

# Fixtures for tests of IOManager
class IOManagerTestBase:

    @pytest.fixture
    def data(self) -> MagicMock:
        """A fake DataManager."""
        return MagicMock()


# Provides a PasswordHasher with a low iteration count
class FastHasherFixture:

    @pytest.fixture
    def hasher(self) -> PasswordHasher:
        return PasswordHasher(iterations=SampleData.FAST_HASH_ITERATIONS)


# Fixtures for tests of AccountService: a fast hasher, a service on fake data, and a registered user
class AccountServiceTestBase(FastHasherFixture):

    @pytest.fixture
    def accounts(self, hasher: PasswordHasher) -> AccountService:
        return AccountServiceFactory(hasher=hasher).create()

    @pytest.fixture
    def alice_uid(self, accounts: AccountService) -> str:
        """The id of an account registered as Alice / pass1!."""
        return accounts.register("Alice", "pass1!", "pass1!").uid

# Helper shared by the prompt tests
class PromptTestBase:

    @staticmethod
    def rejection(prompt: Parser, raw: Any) -> str:
        """The message a prompt rejects an answer with."""
        with pytest.raises(InvalidInput) as problem:
            prompt.parse(raw)
        return str(problem.value)


'''
IOManager
'''

class TestIOManagerAccountActions(IOManagerTestBase):

    @pytest.mark.parametrize("method, args", [
        ("register", ("Alice", "pass1!", "pass1!")),
        ("login", ("Alice", "pass1!")),
        ("change_username", ("123", "Bob")),
        ("change_password", ("123", "pass1!", "new2@", "new2@")),
        ("delete_account", ("123", "pass1!", "DELETE")),
        ("get_username", ("123",)),
    ])
    def test_account_actions_delegate(self, data, method, args):
        # Every account action hands its parameters to AccountService unchanged and returns its result
        accounts = MagicMock()
        app = IOManager(data, accounts=accounts)
        assert getattr(app, method)(*args) is getattr(accounts, method).return_value
        getattr(accounts, method).assert_called_once_with(*args)

    def test_accounts_share_data_manager(self, data):
        # IOManager exposes the DataManager through its AccountService, not a separate data attribute
        app = IOManager(data=data)
        assert app.accounts.data is data


class TestIOManagerSurvey(IOManagerTestBase):

    @pytest.mark.parametrize("answers, expected", [
        (SampleData.ANSWERS,
         SurveyResult(True, "Survey answers accepted.", response=SampleData.RESPONSE)),
        ({**SampleData.ANSWERS, "stress_level": 11, "mood": "Undefined"},
         SurveyResult(False,
                      f"Stress Level: {Messages.RANGE_1_TO_10}; Mood: {Messages.MOOD_CHOICES}",
                      errors={"stress_level": Messages.RANGE_1_TO_10, "mood": Messages.MOOD_CHOICES})),
    ])
    def test_survey_results(self, data, answers, expected):
        # Accepted and rejected survey outcomes
        assert IOManager(data).survey("123", answers) == expected


class TestSendEmail:

    @pytest.fixture(autouse=True)
    def mail_app_context(self):
        # Shared Flask-Mail context setup for the email tests
        with FlaskMailContext():
            yield

    @pytest.fixture
    def mail(self) -> MagicMock:
        return MagicMock()

    @pytest.mark.parametrize("route, subject, opening", [
        ("Urgent support", "Urgent Support Needed", "A Student requires urgent support."),
        ("Counsellor follow-up", "Counsellor Follow up Needed",
         "Our AI has flagged that this student requires counsellor follow-up."),
    ])
    def test_send_email(self, mail, route, subject, opening):
        # Email subject, recipient, and body are selected from the assessment route and score data
        assessment = AssessmentBuilder().with_route(route).build()
        assert IOManager.send_email("counsellor@example.com", "alice", assessment, mail)

        mail.send.assert_called_once()
        message = mail.send.call_args.args[0]
        assert message.subject == subject
        assert message.recipients == ["counsellor@example.com"]
        assert opening in message.body
        assert "Username = alice" in message.body
        assert "Sleep: 7.5 Hr(s)" in message.body
        assert "Mental Wellness Risk Score: 2" in message.body
        assert "Keep taking breaks." in message.body

    def test_send_email_failure(self, caplog, mail):
        # Email delivery failures are logged and surfaced as False
        assessment = AssessmentBuilder().build()
        mail.send.side_effect = RuntimeError("mail server unavailable")

        assert not IOManager.send_email("counsellor@example.com", "alice", assessment, mail)
        mail.send.assert_called_once()
        assert "Failed to send email" in caplog.text


class TestWebAppConstraints:

    PROJECT_ROOT = Path(__file__).resolve().parents[1]

    def test_no_terminal_input_or_output(self):
        # The I/O layer runs inside the web server, so it must not use the terminal:
        # no input() or print() calls in IOManager.py or io_helpers/
        files = ProjectSourceLocator(self.PROJECT_ROOT).files()
        assert len(files) > 5    # the files were found, so the check below means something
        assert ForbiddenCallScanner().find(files) == []


'''
Validators and password hasher
'''

class TestValidators:

    def test_username_errors(self):
        # Valid usernames give no errors; too short, too long, or a character other than
        # letters, numbers, spaces, _ - . gives the username rules
        assert username_errors("Alice") == []
        assert username_errors("a.b_c-d e") == []
        assert username_errors("ab") == [USERNAME_RULES]           # too short
        assert username_errors("a" * 21) == [USERNAME_RULES]       # too long
        assert username_errors("bad!") == [USERNAME_RULES]         # invalid character

    def test_password_errors(self):
        # Each password rule is reported separately
        assert password_errors("ab1!") == []
        assert password_errors("abc") == ["at least 4 characters", "at least one number",
                                          "at least one special character (e.g. ! @ # $ %)"]
        assert password_errors("abcd!") == ["at least one number"]
        assert password_errors("abcd1") == ["at least one special character (e.g. ! @ # $ %)"]


class TestPasswordHasher(FastHasherFixture):

    def test_hasher_round_trip(self, hasher):
        # A hashed password verifies, a wrong one does not, and each hash uses a new salt
        stored = hasher.hash("pass1!")
        assert hasher.verify("pass1!", stored)
        assert not hasher.verify("wrong1!", stored)
        assert hasher.hash("pass1!") != stored

    def test_hasher_rejects_bad_stored_values(self, hasher):
        # Damaged stored hashes return False instead of crashing
        assert not hasher.verify("pass1!", "not-a-hash")
        assert not hasher.verify("pass1!", "sha1$1000$00$00")
        assert not hasher.verify("pass1!", "pbkdf2$abc$zz$zz")
        assert not hasher.verify("pass1!", 123)


'''
# 7. Prompts
'''

class TestTextPrompt(PromptTestBase):

    def test_text_prompt(self):
        # Base text parsing and maximum-length cases for TextPrompt
        assert self.rejection(TextPrompt(), "") == TextPrompt.EMPTY_MESSAGE
        assert self.rejection(TextPrompt(), "   ") == TextPrompt.EMPTY_MESSAGE
        assert self.rejection(TextPrompt(), None) == TextPrompt.EMPTY_MESSAGE    # e.g. a missing form field
        assert TextPrompt().parse("  hello  ") == "hello"

        limited = TextPrompt(max_length=3)
        assert self.rejection(limited, "abcdef") == "Please enter at most 3 characters."
        assert limited.parse("abc") == "abc"


class TestRangePrompt(PromptTestBase):

    def test_range_prompt_int(self):
        # Accepts a whole number given as text or as a number; rejects non-numbers
        # (including True), decimals and out-of-range values
        prompt = RangePrompt(1, 10)
        assert self.rejection(prompt, "abc") == Messages.WHOLE_NUMBER
        assert self.rejection(prompt, "5.5") == Messages.WHOLE_NUMBER
        assert self.rejection(prompt, "11") == Messages.RANGE_1_TO_10
        assert prompt.parse("7") == 7
        assert prompt.parse(7) == 7
        assert self.rejection(prompt, 5.5) == Messages.WHOLE_NUMBER
        assert self.rejection(prompt, True) == Messages.WHOLE_NUMBER

    def test_range_prompt_float(self):
        # With cast=float, accepts decimals and whole numbers, and rejects nan (out of range)
        # and a missing answer (not a number)
        prompt = RangePrompt(0, 24, cast=float)
        assert self.rejection(prompt, "nan") == Messages.RANGE_0_TO_24
        assert prompt.parse("7.5") == 7.5
        assert prompt.parse(8) == 8.0
        assert self.rejection(prompt, None) == "Please enter a valid number."


class TestChoicePrompt(PromptTestBase):

    def test_choice_prompt(self):
        # Returns the option itself, given its number or its name in any letter case
        # (spaces ignored); anything else gets the list of choices
        prompt = ChoicePrompt(["A", "B", "C"])
        assert prompt.parse("2") == "B"
        assert prompt.parse(" b ") == "B"
        assert self.rejection(prompt, "0") == "Please choose one of: A, B, C."
        assert self.rejection(prompt, "D") == "Please choose one of: A, B, C."

    def test_choice_prompt_needs_options(self):
        # A ChoicePrompt needs at least one option
        with pytest.raises(ValueError):
            ChoicePrompt([])


'''
Questionnaire and survey response
'''

class TestQuestionnaire:

    @pytest.fixture
    def questionnaire(self) -> Questionnaire:
        return Questionnaire()

    def test_questionnaire_from_answers(self, questionnaire):
        # from_answers() converts answers given as text (mood by its number) to the right types,
        # and stores the user's id
        response = questionnaire.from_answers("123", {
            "sleep_duration": "7.5", "stress_level": "5", "focus_level": "6", "academic_workload": "4",
            "mood": "2", "social_activity_level": "3", "reflection": "Good week"})
        assert response == SampleData.RESPONSE

    def test_questionnaire_from_chatbot_values(self, questionnaire):
        # The chatbot's values (numbers, mood by name in any case) are accepted, other keys are ignored
        answers = {**SampleData.ANSWERS, "mood": "calm", "text": "Thanks!", "survey_done": True}
        assert questionnaire.from_answers("123", answers) == SampleData.RESPONSE

    def test_questionnaire_reports_every_problem(self, questionnaire):
        # Every invalid or missing answer is reported in question order, with that question's own message
        with pytest.raises(SurveyAnswersError) as problem:
            questionnaire.from_answers("123", {
                "sleep_duration": "25", "stress_level": "5.5", "focus_level": "Focues level",
                "mood": "Undefined", "social_activity_level": "3", "reflection": "x" * 501})
        assert problem.value.errors == {
            "sleep_duration": Messages.RANGE_0_TO_24,
            "stress_level": Messages.WHOLE_NUMBER,
            "focus_level": Messages.WHOLE_NUMBER,
            "academic_workload": Messages.WHOLE_NUMBER,    # missing
            "mood": Messages.MOOD_CHOICES,
            "reflection": "Please enter a reflection with at most 500 characters.",
        }
        assert list(problem.value.errors) == ["sleep_duration", "stress_level", "focus_level",
                                              "academic_workload", "mood", "reflection"]

    @pytest.mark.parametrize("key, answer, expected", SurveyLimitCases.ACCEPTED)
    def test_survey_accepts_limits(self, questionnaire, key, answer, expected):
        # The limits themselves are allowed: sleep 0 and 24 hours, 1 and 10 on every scale,
        # and a mood by number from 1 (the first option) to 5 (the last)
        response = questionnaire.from_answers("123", {**SampleData.ANSWERS, key: answer})
        assert getattr(response, key) == expected

    @pytest.mark.parametrize("key, answer, message", SurveyLimitCases.REJECTED)
    def test_survey_rejects_past_limits(self, questionnaire, key, answer, message):
        # An answer just past a limit is rejected with that question's usual message
        with pytest.raises(SurveyAnswersError) as problem:
            questionnaire.from_answers("123", {**SampleData.ANSWERS, key: answer})
        assert problem.value.errors == {key: message}

    def test_questionnaire_no_answers(self, questionnaire):
        # With no answers at all, every question is reported
        with pytest.raises(SurveyAnswersError) as problem:
            questionnaire.from_answers("123", None)
        assert list(problem.value.errors) == [key for key, _ in questionnaire.questions]
        assert problem.value.errors["reflection"] == TextPrompt.EMPTY_MESSAGE

    def test_questions_match_survey_response(self, questionnaire):
        # The questions match SurveyResponse's corresponding fields exactly
        assert [key for key, _ in questionnaire.questions] == [f.name for f in fields(SurveyResponse)][1:]


class TestSurveyResponse:

    def test_survey_response_to_dict(self):
        # to_dict() gives a plain dictionary of the user id and every answer, with user_id first
        response = SampleData.RESPONSE
        assert response.to_dict() == {
            "user_id": "123", "sleep_duration": 7.5, "stress_level": 5, "focus_level": 6,
            "academic_workload": 4, "mood": "Calm", "social_activity_level": 3, "reflection": "Good week"}
        assert list(response.to_dict())[0] == "user_id"


'''
AccountService (one class per account action)
'''

class TestRegistration(AccountServiceTestBase):

    def test_register_and_login(self, accounts):
        # Register (username saved in lowercase, password hashed), then log in with the same
        # details in other capitals
        registered = accounts.register("Alice", "pass1!", "pass1!")
        assert registered.ok and registered.username == "alice"
        assert registered.message == "Account created successfully!"
        stored = accounts.data.get_users()[0]
        assert stored.get_username() == "alice"
        assert stored.get_password() != "pass1!"

        logged_in = accounts.login("ALICE", "pass1!")
        assert logged_in.ok and logged_in.uid == registered.uid
        assert logged_in.message == "Login successful! Welcome, alice!"

    def test_register_check_order(self, accounts):
        # register() checks the username rules, a taken name, the password rules, then the
        # confirmation, stopping at the first problem; nothing is saved
        assert accounts.register("ab", "x", "y").message == USERNAME_RULES    # username rules first
        accounts.register("Alice", "pass1!", "pass1!")
        assert accounts.register("alice", "x", "y").message == Messages.USERNAME_TAKEN
        assert accounts.register("Bob", "abcd", "y").message == \
            "Password must have at least one number, at least one special character (e.g. ! @ # $ %)."    # password rules
        assert accounts.register("Bob", "pass1!", "").message == "Passwords do not match."    # confirmation
        assert len(accounts.data.get_users()) == 1

    @pytest.mark.parametrize("error", [ConnectionError("down"), ValueError("bad settings")])
    def test_register_connection_error(self, accounts, error):
        # ConnectionError or ValueError from the DB while registering gives the "Unable to connect" msg
        accounts.data.create_user = MagicMock(side_effect=error)
        assert accounts.register("Alice", "pass1!", "pass1!").message == \
            "Unable to connect to the database. Please try again later."

    def test_unexpected_errors_not_hidden(self, accounts):
        # Only the account checks' own errors become a failed result. Anything unexpected (e.g. a bug)
        # is still raised, so Flask logs it instead of the web page showing a misleading message
        accounts.data.create_user = MagicMock(side_effect=RuntimeError("bug"))
        with pytest.raises(RuntimeError):
            accounts.register("Alice", "pass1!", "pass1!")


class TestLogin(AccountServiceTestBase):

    def test_login_failures(self, accounts):
        # Failed logins return ok=False with the login page's messages
        assert accounts.login("Alice", "pass1!").message == "No users registered yet. Please register first."
        accounts.register("Alice", "pass1!", "pass1!")
        assert accounts.login("Alice", "wrong1!").message == "Invalid username or password."
        assert accounts.login("Nobody", "pass1!").message == "Invalid username or password."

    def test_login_ignores_case(self, accounts, hasher):
        # Usernames match in any letter case
        # When accounts differ only in letter case
        # an exact match wins, then the lowercase one
        # and the name can't be registered again in other capitals
        accounts.data.users.append(UserRecord("Marcus", hasher.hash("pass1!")))
        assert accounts.login("marcus", "pass1!").ok
        assert accounts.login("MARCUS", "pass1!").username == "Marcus"
        assert accounts.register("marcus", "pass1!", "pass1!").message == Messages.USERNAME_TAKEN

        accounts.data.users += [UserRecord("Alice", hasher.hash("upper1!")),
                                UserRecord("alice", hasher.hash("lower1!"))]
        assert accounts.login("Alice", "upper1!").username == "Alice"
        assert accounts.login("alice", "lower1!").username == "alice"
        assert accounts.login("ALICE", "lower1!").username == "alice"


class TestCredentialChanges(AccountServiceTestBase):

    def test_change_username_and_password(self, accounts, alice_uid):
        # Successful changes: the new username is saved in lowercase (the user's own name in other
        # capitals is allowed), the new password logs in, and each gives its success message
        assert accounts.change_username(alice_uid, "ALICE").ok    # user's own name is harmless
        changed = accounts.change_username(alice_uid, "Carol")
        assert changed.ok and changed.username == "carol"
        assert changed.message == "Your username has been successfully updated!"
        assert accounts.data.get_user_by_id(alice_uid).get_username() == "carol"
        changed = accounts.change_password(alice_uid, "pass1!", "new2@", "new2@")
        assert changed.ok and changed.message == "Your password has been successfully updated!"
        assert accounts.login("Carol", "new2@").ok

    def test_change_password_check_order(self, accounts, alice_uid):
        # change_password reports the earliest applicable validation error in a fixed order
        assert accounts.change_password("nope", "", "", "").message == "Current user not found."    # 1. the account
        assert accounts.change_password(alice_uid, "", "", "").message == "Please enter your old password"    # 2. current entered
        assert accounts.change_password(alice_uid, "wrong1!", "a", "a").message == "Incorrect password. Please try again."    # 3. current correct
        assert accounts.change_password(alice_uid, "pass1!", "", "x").message == "Please enter your new password"    # 4. new entered
        assert accounts.change_password(alice_uid, "pass1!", "a", "").message == Messages.PASSWORD_RULES_ALL    # 5. the rules, before the confirmation
        assert accounts.change_password(alice_uid, "pass1!", "a", "b").message == Messages.PASSWORD_RULES_ALL    # ... and before the match
        assert accounts.change_password(alice_uid, "pass1!", "new2@", "").message == \
            "Please confirm your new password"    # 6. confirmation entered, before the match
        accounts.data.fail_saves = True
        assert accounts.change_password(alice_uid, "pass1!", "new2@", "new3@").message == \
            "Your new password & confirmation do not match."    # 7. the match, before saving
        assert accounts.login("alice", "pass1!").ok    # the password was never changed

    def test_change_username_check_order(self, accounts, alice_uid):
        # change_username reports account, empty-name, rules, and duplicate-name errors in order.
        # A failed username save is covered by TestAccountServiceRobustness.test_unknown_user_and_failed_saves.
        accounts.register("Bob", "pass1!", "pass1!")
        accounts.data.users.append(UserRecord("old!", "hash"))    # an old account whose name breaks today's rules
        assert accounts.change_username("nope", "").message == "Current user not found."
        assert accounts.change_username(alice_uid, None).message == "Please Enter a username"
        assert accounts.change_username(alice_uid, "  ").message == "Please Enter a username"
        assert accounts.change_username(alice_uid, "OLD!").message == USERNAME_RULES    # the rules, before a taken name
        accounts.data.fail_saves = True
        assert accounts.change_username(alice_uid, "BOB").message == Messages.USERNAME_TAKEN    # a taken name, before saving
        assert accounts.get_username(alice_uid) == "alice"


class TestAccountDeletion(AccountServiceTestBase):

    def test_delete_account(self, accounts, alice_uid):
        # Account deletion requires both valid credentials and the exact confirmation text
        assert accounts.delete_account(alice_uid, "wrong1!", "DELETE").message == \
            "Incorrect password. Your account was not deleted."
        assert accounts.delete_account(alice_uid, "pass1!", "delete").message == \
            "Type DELETE in capital letters to confirm."
        assert accounts.get_username(alice_uid) == "alice"

        deleted = accounts.delete_account(alice_uid, "pass1!", "DELETE")
        assert deleted.ok and deleted.message == "Your account has been deleted."
        assert accounts.get_username(alice_uid) is None

    def test_delete_account_failed_save(self, accounts, alice_uid):
        # A failed persistence operation is returned as an account failure, not reported as success
        accounts.data.fail_saves = True

        result = accounts.delete_account(alice_uid, "pass1!", "DELETE")
        assert not result.ok
        assert result.message == "There was an error deleting your account. Please try again later."


class TestAccountServiceRobustness(AccountServiceTestBase):

    def test_account_answers_trimmed_or_missing(self, accounts):
        # Every answer is trimmed (username, password, confirmation, current and new password),
        # and a missing answer (None) counts as empty.
        registered = accounts.register("  Alice  ", " pass1! ", "  pass1!  ")
        assert registered.ok and accounts.data.get_users()[0].get_username() == "alice"
        assert accounts.login(" alice ", "pass1! ").ok
        assert accounts.change_password(registered.uid, " pass1! ", " new2@ ", "new2@  ").ok
        assert accounts.login("alice", "new2@").ok         # the new password was saved without the spaces
        assert accounts.register(None, None, None).message == USERNAME_RULES
        assert accounts.register("Bob", None, None).message == Messages.PASSWORD_RULES_ALL
        assert accounts.login(None, None).message == "Invalid username or password."

    def test_account_actions_keyword_arguments(self, accounts):
        # Account actions also accept their answers by name
        uid = accounts.register(username="Alice", password="pass1!", confirm="pass1!").uid
        assert accounts.change_password(uid=uid, current_password="pass1!",
                                        new_password="new2@", confirm="new2@").ok

    def test_unknown_user_and_failed_saves(self, accounts):
        # get_username() gives None for an unknown user id, and a failed save gives each action's
        # error message instead of crashing
        assert accounts.get_username("nope") is None
        uid = accounts.register("Alice", "pass1!", "pass1!").uid
        assert accounts.get_username(uid) == "alice"

        accounts.data.fail_saves = True
        assert accounts.register("Bob", "pass1!", "pass1!").message == \
            "Could not create your account. Please try again."
        assert accounts.change_username(uid, "carol").message == \
            "There was an error with updating your username. Please try again."
        assert accounts.change_password(uid, "pass1!", "new2@", "new2@").message == \
            "There has been an issue with updating your password. Please try again later"