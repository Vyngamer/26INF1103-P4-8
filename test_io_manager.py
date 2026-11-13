from unittest.mock import MagicMock
import pytest
from io_manager import IOManager
from io_helpers.account_service import AccountService
from data_manager_helper.UserRecord import UserRecord
from io_helpers.hasher import PasswordHasher
from io_helpers.validators import username_errors, password_errors, USERNAME_RULES
from io_helpers.prompts import TextPrompt, RangePrompt, ChoicePrompt, InvalidInput
from io_helpers.survey_response import SurveyResponse, SurveyResult
from io_helpers.questionnaire import Questionnaire, SurveyAnswersError

# Sample completed survey, used by the survey tests below
SAMPLE_RESPONSE = SurveyResponse("123", 7.5, 5, 6, 4, "Calm", 3, "Good week")

# SAMPLE_RESPONSE's answers without the user id, as the web app passes them to survey()
SAMPLE_ANSWERS = {key: value for key, value in SAMPLE_RESPONSE.to_dict().items() if key != "user_id"}

PASSWORD_RULES_ALL = "Password must have at least 4 characters, at least one number, at least one special character (e.g. ! @ # $ %)."
MOOD_CHOICES = "Please choose one of: Motivated, Calm, Anxious, Sad, Exhausted."
SCALE_KEYS = ("stress_level", "focus_level", "academic_workload", "social_activity_level")

# Mock record
def fake_record(record_id="r1"):
    record = MagicMock()
    record.get_record_id.return_value = record_id
    return record

# Mock DataManager that returns the given records
def fake_data(records=()):
    data = MagicMock()
    data.get_user_records.return_value = list(records)
    return data

# The message a prompt rejects an answer with
def rejection(prompt, raw):
    with pytest.raises(InvalidInput) as problem:
        prompt.parse(raw)
    return str(problem.value)

# --- IOManager Tests ---

# Every account action on IOManager hands its parameters to AccountService unchanged and returns its result
@pytest.mark.parametrize("method, args", [
    ("register", ("Alice", "pass1!", "pass1!")),
    ("login", ("Alice", "pass1!")),
    ("change_username", ("123", "Bob")),
    ("change_password", ("123", "pass1!", "new2@", "new2@")),
    ("get_username", ("123",)),
])
def test_account_actions_delegate(method, args):
    accounts = MagicMock()
    app = IOManager(fake_data(), accounts=accounts)
    assert getattr(app, method)(*args) is getattr(accounts, method).return_value
    getattr(accounts, method).assert_called_once_with(*args)

# IOManager builds its AccountService in __init__, with the same DataManager
def test_accounts_share_data_manager():
    data = fake_data()
    app = IOManager(data=data)
    assert app.data is data
    assert app.accounts.data is data

# --- Survey Tests ---

# Valid answers come back in an accepted SurveyResult, and are handed to process_responses (if given) with the user's id
def test_survey_valid_answers():
    expected = SurveyResult(True, "Survey answers accepted.", response=SAMPLE_RESPONSE)
    received = []
    app = IOManager(fake_data(), process_responses=lambda uid, responses: received.append((uid, responses)))
    assert app.survey("123", SAMPLE_ANSWERS) == expected
    assert received == [("123", SAMPLE_RESPONSE)]
    assert IOManager(fake_data()).survey("123", SAMPLE_ANSWERS) == expected    # also works without process_responses

# Invalid answers are reported, one message per question, and never handed on
def test_survey_invalid_answers_not_passed_on():
    received = []
    app = IOManager(fake_data(), process_responses=lambda uid, responses: received.append(responses))
    result = app.survey("123", {**SAMPLE_ANSWERS, "stress_level": 11, "mood": "Undefined"})

    assert not result.ok and result.response is None
    assert result.errors == {"stress_level": "Please enter a number from 1 to 10.", "mood": MOOD_CHOICES}
    assert result.message == f"Stress Level: Please enter a number from 1 to 10.; Mood: {MOOD_CHOICES}"
    assert received == []

# --- Validator Tests ---

# Valid usernames give no errors; too short, too long, 
# or a character other than letters, numbers, spaces, _ - . gives the username rules
def test_username_errors():
    assert username_errors("Alice") == []
    assert username_errors("a.b_c-d e") == []
    assert username_errors("ab") == [USERNAME_RULES]           # too short
    assert username_errors("a" * 21) == [USERNAME_RULES]       # too long
    assert username_errors("bad!") == [USERNAME_RULES]         # invalid character

# Check that each password rule is reported separately
def test_password_errors():
    assert password_errors("ab1!") == []
    assert password_errors("abc") == ["at least 4 characters", "at least one number",
                                      "at least one special character (e.g. ! @ # $ %)"]
    assert password_errors("abcd!") == ["at least one number"]
    assert password_errors("abcd1") == ["at least one special character (e.g. ! @ # $ %)"]

# --- Password Hasher Tests ---

# Check that a hashed password verifies, a wrong one does not, and each hash uses a new salt
def test_hasher_round_trip():
    hasher = PasswordHasher(iterations=1000)
    stored = hasher.hash("pass1!")
    assert hasher.verify("pass1!", stored)
    assert not hasher.verify("wrong1!", stored)
    assert hasher.hash("pass1!") != stored

# Check that damaged stored hashes return False instead of crashing
def test_hasher_rejects_bad_stored_values():
    hasher = PasswordHasher(iterations=1000)
    assert not hasher.verify("pass1!", "not-a-hash")
    assert not hasher.verify("pass1!", "sha1$1000$00$00")
    assert not hasher.verify("pass1!", "pbkdf2$abc$zz$zz")
    assert not hasher.verify("pass1!", 123)

# --- Prompt Tests ---

# TextPrompt rejects an empty answer and trims whitespace
def test_text_prompt():
    assert rejection(TextPrompt(), "") == TextPrompt.EMPTY_MESSAGE
    assert rejection(TextPrompt(), "   ") == TextPrompt.EMPTY_MESSAGE
    assert rejection(TextPrompt(), None) == TextPrompt.EMPTY_MESSAGE    # e.g. a missing form field
    assert TextPrompt().parse("  hello  ") == "hello"

# TextPrompt with a limit accepts an answer at the limit and rejects a longer one
def test_text_prompt_max_length():
    assert rejection(TextPrompt(max_length=3), "abcdef") == "Please enter at most 3 characters."
    assert TextPrompt(max_length=3).parse("abc") == "abc"

# RangePrompt accepts a whole number given as text or as a number, and rejects non-numbers
# (including True), decimals and out-of-range values
def test_range_prompt_int():
    prompt = RangePrompt(1, 10)
    assert rejection(prompt, "abc") == "Please enter a whole number."
    assert rejection(prompt, "5.5") == "Please enter a whole number."
    assert rejection(prompt, "11") == "Please enter a number from 1 to 10."
    assert prompt.parse("7") == 7
    assert prompt.parse(7) == 7
    assert rejection(prompt, 5.5) == "Please enter a whole number."
    assert rejection(prompt, True) == "Please enter a whole number."

# RangePrompt with cast=float accepts decimals and whole numbers, and rejects nan (out of range)
# and a missing answer (not a number)
def test_range_prompt_float():
    prompt = RangePrompt(0, 24, cast=float)
    assert rejection(prompt, "nan") == "Please enter a number from 0 to 24."
    assert prompt.parse("7.5") == 7.5
    assert prompt.parse(8) == 8.0
    assert rejection(prompt, None) == "Please enter a valid number."

# ChoicePrompt returns the option itself, given its number or its name in any letter case
# (spaces ignored); anything else gets the list of choices
def test_choice_prompt():
    prompt = ChoicePrompt(["A", "B", "C"])
    assert prompt.parse("2") == "B"
    assert prompt.parse(" b ") == "B"
    assert rejection(prompt, "0") == "Please choose one of: A, B, C."
    assert rejection(prompt, "D") == "Please choose one of: A, B, C."

# ChoicePrompt needs at least one option
def test_choice_prompt_needs_options():
    with pytest.raises(ValueError):
        ChoicePrompt([])

# --- Questionnaire Tests ---

# from_answers() converts answers given as text (mood by its number) to the right types, and stores the user's id
def test_questionnaire_from_answers():
    response = Questionnaire().from_answers("123", {
        "sleep_duration": "7.5", "stress_level": "5", "focus_level": "6", "academic_workload": "4",
        "mood": "2", "social_activity_level": "3", "reflection": "Good week"})
    assert response == SAMPLE_RESPONSE

# The chatbot's values (numbers, mood by name in any case) are accepted, other keys are ignored
def test_questionnaire_from_chatbot_values():
    answers = {**SAMPLE_ANSWERS, "mood": "calm", "text": "Thanks!", "survey_done": True}
    assert Questionnaire().from_answers("123", answers) == SAMPLE_RESPONSE

# Every invalid or missing answer is reported in question order, with that question's own message
def test_questionnaire_reports_every_problem():
    with pytest.raises(SurveyAnswersError) as problem:
        Questionnaire().from_answers("123", {
            "sleep_duration": "25", "stress_level": "5.5", "focus_level": "Focues level",
            "mood": "Undefined", "social_activity_level": "3", "reflection": "x" * 501})
    assert problem.value.errors == {
        "sleep_duration": "Please enter a number from 0 to 24.",
        "stress_level": "Please enter a whole number.",
        "focus_level": "Please enter a whole number.",
        "academic_workload": "Please enter a whole number.",    # missing
        "mood": MOOD_CHOICES,
        "reflection": "Please enter a reflection with at most 500 characters.",
    }
    assert list(problem.value.errors) == ["sleep_duration", "stress_level", "focus_level",
                                          "academic_workload", "mood", "reflection"]

# The scale limits themselves are allowed: sleep 0 and 24 hours, 1 and 10 on every scale,
# and a mood by number from 1 (the first option) to 5 (the last)
@pytest.mark.parametrize("key, answer, expected",
    [("sleep_duration", "0", 0), ("sleep_duration", "24", 24)]
    + [(key, answer, int(answer)) for key in SCALE_KEYS for answer in ("1", "10")]
    + [("mood", "1", "Motivated"), ("mood", "5", "Exhausted")])
def test_survey_accepts_limits(key, answer, expected):
    response = Questionnaire().from_answers("123", {**SAMPLE_ANSWERS, key: answer})
    assert getattr(response, key) == expected

# An answer just past a limit is rejected with that question's usual message
@pytest.mark.parametrize("key, answer, message",
    [("sleep_duration", "-0.5", "Please enter a number from 0 to 24."),
     ("sleep_duration", "24.5", "Please enter a number from 0 to 24.")]
    + [(key, answer, "Please enter a number from 1 to 10.") for key in SCALE_KEYS for answer in ("0", "11")]
    + [("mood", "0", MOOD_CHOICES), ("mood", "6", MOOD_CHOICES)])
def test_survey_rejects_past_limits(key, answer, message):
    with pytest.raises(SurveyAnswersError) as problem:
        Questionnaire().from_answers("123", {**SAMPLE_ANSWERS, key: answer})
    assert problem.value.errors == {key: message}

# With no answers at all, every question is reported
def test_questionnaire_no_answers():
    with pytest.raises(SurveyAnswersError) as problem:
        Questionnaire().from_answers("123", None)
    assert list(problem.value.errors) == [key for key, _ in Questionnaire().questions]
    assert problem.value.errors["reflection"] == TextPrompt.EMPTY_MESSAGE

# Check that the questions match SurveyResponse's corresponding fields exactly
def test_questions_match_survey_response():
    from dataclasses import fields
    assert [key for key, _ in Questionnaire().questions] == [f.name for f in fields(SurveyResponse)][1:]

# --- Survey Response Tests ---

# to_dict() gives a plain dictionary of the user id and every answer, with user_id first
def test_survey_response_to_dict():
    assert SAMPLE_RESPONSE.to_dict() == {
        "user_id": "123", "sleep_duration": 7.5, "stress_level": 5, "focus_level": 6,
        "academic_workload": 4, "mood": "Calm", "social_activity_level": 3, "reflection": "Good week"}
    assert list(SAMPLE_RESPONSE.to_dict())[0] == "user_id"

# --- Account Service Tests ---

# Stand-in for DataManager's user methods, behaving like UserManager + MongoDBStorage
class FakeUserData:
    def __init__(self):
        self.users = []
        self.fail_saves = False    # set True to act like a MongoDB error

    def get_users(self):
        return self.users.copy()

    def get_user_by_id(self, user_id):
        return next((u for u in self.users if u.get_user_id() == user_id), None)

    def _taken(self, username, uid=None):
        return any(u.get_username() == username and u.get_user_id() != uid for u in self.users)

    def create_user(self, username, password):
        if self.fail_saves or self._taken(username):
            return None
        user = UserRecord(username, password)
        self.users.append(user)
        return user.get_user_id()

    def update_user(self, user_id, updates):
        user = self.get_user_by_id(user_id)
        if self.fail_saves or ("username" in updates and self._taken(updates["username"], user_id)):
            return False
        data = {**user.to_dict(), **updates}
        self.users[self.users.index(user)] = UserRecord(data["username"], data["password"], user_id)
        return True


# AccountService with a fake DataManager and a fast hasher
def make_accounts():
    return AccountService(FakeUserData(), PasswordHasher(iterations=1000))

# Register (username saved in lowercase, password hashed), then log in with the same details in other capitals
def test_register_and_login():
    accounts = make_accounts()
    registered = accounts.register("Alice", "pass1!", "pass1!")
    assert registered.ok and registered.username == "alice"
    assert registered.message == "Account created successfully!"
    stored = accounts.data.get_users()[0]
    assert stored.get_username() == "alice"
    assert stored.get_password() != "pass1!"

    logged_in = accounts.login("ALICE", "pass1!")
    assert logged_in.ok and logged_in.uid == registered.uid
    assert logged_in.message == "Login successful! Welcome, alice!"

# Failed logins return ok=False with the login page's messages
def test_login_failures():
    accounts = make_accounts()
    assert accounts.login("Alice", "pass1!").message == "No users registered yet. Please register first."
    accounts.register("Alice", "pass1!", "pass1!")
    assert accounts.login("Alice", "wrong1!").message == "Invalid username or password."
    assert accounts.login("Nobody", "pass1!").message == "Invalid username or password."

# register() checks the username rules, a taken name, the password rules, then the confirmation,
# stopping at the first problem; nothing is saved
def test_register_check_order():
    accounts = make_accounts()
    assert accounts.register("ab", "x", "y").message == USERNAME_RULES    # username rules first
    accounts.register("Alice", "pass1!", "pass1!")
    assert accounts.register("alice", "x", "y").message == "This username already exists. Please choose another."
    assert accounts.register("Bob", "abcd", "y").message == \
        "Password must have at least one number, at least one special character (e.g. ! @ # $ %)."    # then the password rules
    assert accounts.register("Bob", "pass1!", "").message == "Passwords do not match."    # then the confirmation
    assert len(accounts.data.get_users()) == 1

# Every answer is trimmed (username, password, confirmation, current and new password),
# and a missing answer (None) counts as empty
def test_account_answers_trimmed_or_missing():
    accounts = make_accounts()
    registered = accounts.register("  Alice  ", " pass1! ", "  pass1!  ")
    assert registered.ok and accounts.data.get_users()[0].get_username() == "alice"
    assert accounts.login(" alice ", "pass1! ").ok
    assert accounts.change_password(registered.uid, " pass1! ", " new2@ ", "new2@  ").ok
    assert accounts.login("alice", "new2@").ok         # the new password was saved without the spaces
    assert accounts.register(None, None, None).message == USERNAME_RULES
    assert accounts.register("Bob", None, None).message == PASSWORD_RULES_ALL
    assert accounts.login(None, None).message == "Invalid username or password."

# Usernames match in any letter case, so accounts saved with capitals (e.g. by the old web pages) still log in.
# When accounts differ only in letter case, an exact match wins, then the lowercase one,
# and the name can't be registered again in other capitals (CHANGED: added this last part)
def test_login_ignores_case():
    hasher = PasswordHasher(iterations=1000)
    accounts = make_accounts()
    accounts.data.users.append(UserRecord("Marcus", hasher.hash("pass1!")))
    assert accounts.login("marcus", "pass1!").ok
    assert accounts.login("MARCUS", "pass1!").username == "Marcus"
    assert accounts.register("marcus", "pass1!", "pass1!").message == "This username already exists. Please choose another."

    accounts.data.users += [UserRecord("Alice", hasher.hash("upper1!")), UserRecord("alice", hasher.hash("lower1!"))]
    assert accounts.login("Alice", "upper1!").username == "Alice"
    assert accounts.login("alice", "lower1!").username == "alice"
    assert accounts.login("ALICE", "lower1!").username == "alice"

# Successful changes: the new username is saved in lowercase (user's own name in other capitals is allowed),
# the new password logs in, and each gives its success message
def test_change_username_and_password():
    accounts = make_accounts()
    uid = accounts.register("Alice", "pass1!", "pass1!").uid
    assert accounts.change_username(uid, "ALICE").ok    # the user's own name is harmless
    changed = accounts.change_username(uid, "Carol")
    assert changed.ok and changed.username == "carol"
    assert changed.message == "Your username has been successfully updated!"
    assert accounts.data.get_user_by_id(uid).get_username() == "carol"
    changed = accounts.change_password(uid, "pass1!", "new2@", "new2@")
    assert changed.ok and changed.message == "Your password has been successfully updated!"
    assert accounts.login("Carol", "new2@").ok

# change_password stops at the first problem, in a fixed order.
# each call has at least two problems, and the earliest check's message must be the one shown
def test_change_password_check_order():
    accounts = make_accounts()
    uid = accounts.register("Alice", "pass1!", "pass1!").uid
    assert accounts.change_password("nope", "", "", "").message == "Current user not found."    # 1. the account
    assert accounts.change_password(uid, "", "", "").message == "Please enter your old password"    # 2. current entered
    assert accounts.change_password(uid, "wrong1!", "a", "a").message == "Incorrect password. Please try again."    # 3. current correct
    assert accounts.change_password(uid, "pass1!", "", "x").message == "Please enter your new password"    # 4. new entered
    assert accounts.change_password(uid, "pass1!", "a", "").message == PASSWORD_RULES_ALL    # 5. the rules, before the confirmation
    assert accounts.change_password(uid, "pass1!", "a", "b").message == PASSWORD_RULES_ALL    # ... and before the match
    assert accounts.change_password(uid, "pass1!", "new2@", "").message == \
        "Please confirm your new password"    # 6. confirmation entered, before the match
    accounts.data.fail_saves = True
    assert accounts.change_password(uid, "pass1!", "new2@", "new3@").message == \
        "Your new password & confirmation do not match."    # 7. the match, before saving
    assert accounts.login("alice", "pass1!").ok    # the password was never changed

# change_username stops at the first problem: the account, an empty name, the rules, a taken name, then saving
def test_change_username_check_order():
    accounts = make_accounts()
    uid = accounts.register("Alice", "pass1!", "pass1!").uid
    accounts.register("Bob", "pass1!", "pass1!")
    accounts.data.users.append(UserRecord("old!", "hash"))    # an old account whose name breaks today's rules
    assert accounts.change_username("nope", "").message == "Current user not found."
    assert accounts.change_username(uid, None).message == "Please Enter a username"
    assert accounts.change_username(uid, "  ").message == "Please Enter a username"
    assert accounts.change_username(uid, "OLD!").message == USERNAME_RULES    # the rules, before a taken name
    accounts.data.fail_saves = True
    assert accounts.change_username(uid, "BOB").message == "This username already exists. Please choose another."    # a taken name, before saving
    assert accounts.get_username(uid) == "alice"

# get_username() gives None for unknown user id, and a failed save gives each action's error msg instead of crashing
def test_unknown_user_and_failed_saves():
    accounts = make_accounts()
    assert accounts.get_username("nope") is None
    uid = accounts.register("Alice", "pass1!", "pass1!").uid
    assert accounts.get_username(uid) == "alice"

    accounts.data.fail_saves = True
    assert accounts.register("Bob", "pass1!", "pass1!").message == "Could not create your account. Please try again."
    assert accounts.change_username(uid, "carol").message == "There was an error with updating your username. Please try again."
    assert accounts.change_password(uid, "pass1!", "new2@", "new2@").message == "There has been an issue with updating your password. Please try again later"

# ConnectionError or ValueError from the DB while registering gives the "Unable to connect" msg
@pytest.mark.parametrize("error", [ConnectionError("down"), ValueError("bad settings")])
def test_register_connection_error(error):
    accounts = make_accounts()
    accounts.data.create_user = MagicMock(side_effect=error)
    assert accounts.register("Alice", "pass1!", "pass1!").message == "Unable to connect to the database. Please try again later."

# Only the account checks' own errors become a failed result
# Anything unexpected (e.g. a bug) still raised, so Flask logs it instead of web page showing a misleading message
def test_unexpected_errors_not_hidden():
    accounts = make_accounts()
    accounts.data.create_user = MagicMock(side_effect=RuntimeError("bug"))
    with pytest.raises(RuntimeError):
        accounts.register("Alice", "pass1!", "pass1!")

# Account actions also accept their answers by name
def test_account_actions_keyword_arguments():
    accounts = make_accounts()
    uid = accounts.register(username="Alice", password="pass1!", confirm="pass1!").uid
    assert accounts.change_password(uid=uid, current_password="pass1!", new_password="new2@", confirm="new2@").ok

# --- Trends Tests ---

# With fewer than 2 records there is no trend data; with 2 or more, it comes from get_user_int_records(), oldest -> newest
def test_trends():
    data = fake_data([fake_record()])
    assert IOManager(data).trends("123") is None
    data.get_user_int_records.assert_not_called()

    records = [fake_record("new"), fake_record("old")]
    data = fake_data(records)
    data.get_user_int_records.return_value = [{"date": "02-01-2026"}, {"date": "01-01-2026"}]
    assert IOManager(data).trends("123") == [{"date": "01-01-2026"}, {"date": "02-01-2026"}]
    data.get_user_int_records.assert_called_once_with(records, "123")

# trends() never calls load_records(), which would download every user's records from MongoDB again
def test_trends_do_not_reload_records():
    data = fake_data([fake_record("b"), fake_record("a")])
    data.get_user_int_records.return_value = []
    IOManager(data).trends("123")
    data.load_records.assert_not_called()

# --- Web App Tests ---

# The I/O layer runs inside the web server, so it must not use the terminal:
# no input() or print() calls in io_manager.py or io_helpers/
def test_no_terminal_input_or_output():
    import ast
    from pathlib import Path
    folder = Path(__file__).parent
    files = [folder / "io_manager.py", *sorted((folder / "io_helpers").glob("*.py"))]
    assert len(files) > 5    # the files were found, so the check below means something

    calls = [f"{path.name}:{node.lineno} {node.func.id}()"
             for path in files
             for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("input", "print")]
    assert calls == []