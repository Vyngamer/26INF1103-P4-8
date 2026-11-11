from unittest.mock import MagicMock
import pytest
from datetime import datetime
from io_manager import IOManager
from io_helpers.history import todays_records, history_records, latest_record, find_record
from io_helpers.account_models import AccountResult
from io_helpers.account_service import AccountService
from data_manager_helper.UserRecord import UserRecord
from io_helpers.hasher import PasswordHasher
from io_helpers.validators import username_errors, password_errors, USERNAME_RULES
from io_helpers.prompts import TextPrompt, RangePrompt, ChoicePrompt, InvalidInput
from io_helpers.trends import trend_points, MIN_RECORDS
from io_helpers.survey_response import SurveyResponse, SurveyResult
from io_helpers.questionnaire import Questionnaire, SurveyAnswersError

# Sample completed survey, used by the survey tests below
SAMPLE_RESPONSE = SurveyResponse("123", 7.5, 5, 6, 4, "Calm", 3, "Good week")

# Same answers as the web app would pass them in
SAMPLE_ANSWERS = {key: value for key, value in SAMPLE_RESPONSE.to_dict().items() if key != "user_id"}

PASSWORD_RULES_ALL = "at least 4 characters at least one number at least one special character (e.g. ! @ # $ %)"
MOOD_CHOICES = "Please choose one of: Motivated, Calm, Anxious, Sad, Exhausted."
USERNAME_TAKEN = "This username already exists. Please choose another."

def fake_record(date="01-01-2026", time="10:00:00", record_id="r1"):
    record = MagicMock()
    record.get_date.return_value = date
    record.get_time.return_value = time
    record.get_record_id.return_value = record_id
    record.get_user_input.return_value = SAMPLE_RESPONSE.to_dict()
    record.get_ai_output.return_value = {
        "mental_wellness_risk_score": 40, "burnout_risk_score": 55, "sentiment": "Neutral",
        "crisis_alert": False, "primary_stressor": "Exams", "personalized_recommendations": "Take breaks"}
    record.get_logic_output.return_value = {
        "mental_wellness_risk_tier": "Moderate", "route": "Self-help", "warnings": [],
        "counselling_recommendation": False, "display_messages": []}
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

# --- Action Tests ---

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

# --- Survey Tests ---

# Survey() checks the given answers, then hands them to process_responses with user id
def test_survey_passes_responses_to_function():
    received = []
    app = IOManager(fake_data(), process_responses=lambda uid, responses: received.append((uid, responses)))
    result = app.survey("123", SAMPLE_ANSWERS)

    assert result.ok and result.response == SAMPLE_RESPONSE
    assert received == [("123", SAMPLE_RESPONSE)]

# Survey() still works without a process_responses function
def test_survey_without_function():
    result = IOManager(fake_data()).survey("123", SAMPLE_ANSWERS)
    assert result == SurveyResult(True, "Survey answers accepted.", response=SAMPLE_RESPONSE)

# Invalid answers are reported, one message per question, and never handed on
def test_survey_invalid_answers_not_passed_on():
    received = []
    app = IOManager(fake_data(), process_responses=lambda uid, responses: received.append(responses))
    result = app.survey("123", {**SAMPLE_ANSWERS, "stress_level": 11, "mood": "Undefined"})

    assert not result.ok and result.response is None
    assert result.errors == {"stress_level": "Please enter a number from 1 to 10.", "mood": MOOD_CHOICES}
    assert result.message == f"Stress Level: Please enter a number from 1 to 10.; Mood: {MOOD_CHOICES}"
    assert received == []

# --- History Tests ---

# With no records the history is an empty list
def test_history_no_records():
    assert IOManager(data=fake_data([])).history("123") == []

# find_record() picks one of the user's records by its id
def test_find_record():
    records = [fake_record(time="15:00:00", record_id="b"), fake_record(time="10:00:00", record_id="a")]
    data = fake_data(records)
    data.get_user_records.side_effect = lambda uid: records if uid == "123" else []
    app = IOManager(data=data)

    assert app.find_record("123", "a") is records[1]
    assert app.find_record("123", "zzz") is None
    assert app.find_record("123", None) is None
    assert app.find_record("456", "a") is None    # another user's record is never returned

# Check that todays_records() keeps only records dated today, in the same (newest first) order
def test_todays_records():
    from datetime import datetime
    today = datetime.now().strftime("%d-%m-%Y")
    records = [fake_record(today, "15:00:00"), fake_record("01-01-2000", "09:00:00"), fake_record(today, "10:00:00")]
    data = fake_data(records)
    assert todays_records(data, "123") == [records[0], records[2]]
    data.get_user_records.assert_called_once_with("123")

# The user's own records, in the stored (newest first) order
def test_history_records():
    records = [fake_record("02-01-2026", "09:30:00", "b"), fake_record("01-01-2026", "10:00:00", "a")]
    data = fake_data(records)
    history = IOManager(data=data).history("123")

    data.get_user_records.assert_called_once_with("123")
    assert history == records
    assert all(shown is record for shown, record in zip(history, records))

# Today's assessment is in the history
def test_history_includes_today():
    today = datetime.now().strftime("%d-%m-%Y")
    records = history_records(fake_data([fake_record(today, record_id="t")]), "123")
    assert [record.get_record_id() for record in records] == ["t"]

# latest_record() is the newest record, or None when there are none
def test_latest_record():
    records = [fake_record(record_id="new"), fake_record(record_id="old")]
    assert IOManager(fake_data(records)).latest_record("123") is records[0]
    assert latest_record(fake_data([]), "123") is None

# Stand-in for MongoDBStorage that only loads the given assessment documents
class FakeAssessmentStorage:
    def __init__(self, documents):
        self.documents = documents

    def load(self):
        return list(self.documents)

# One stored assessment document, in the format AssessmentManager loads
def assessment_document(record_id, date, user_id="123"):
    return {"record_id": record_id, "date": date, "time": "09:00:00",
            "user_input": {**SAMPLE_RESPONSE.to_dict(), "user_id": user_id},
            "ai_output": {"mental_wellness_risk_score": 40, "burnout_risk_score": 50},
            "logic_output": {"warnings": [], "display_messages": []}}

# Check that with the real AssessmentManager, history is newest first and trends oldest first,
# whatever order the documents are stored in, and that other users' records are never included
def test_history_and_trends_with_real_assessment_manager():
    from data_manager_helper.AssessmentManager import AssessmentManager
    data = AssessmentManager(FakeAssessmentStorage([
        assessment_document("b", "13-10-2026"), assessment_document("a", "10-10-2026"),
        assessment_document("x", "11-10-2026", user_id="other"), assessment_document("c", "17-10-2026")]))
    app = IOManager(data)

    assert [record.get_record_id() for record in app.history("123")] == ["c", "b", "a"]
    assert [point["date"] for point in app.trends("123")] == ["10-10-2026", "13-10-2026", "17-10-2026"]
    assert app.latest_record("123").get_record_id() == "c"
    assert find_record(data, "123", "x") is None

# --- Validator Tests ---

# Test valid and invalid usernames
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
    assert rejection(TextPrompt("> "), "") == TextPrompt.EMPTY_MESSAGE
    assert rejection(TextPrompt("> "), "   ") == TextPrompt.EMPTY_MESSAGE
    assert rejection(TextPrompt("> "), None) == TextPrompt.EMPTY_MESSAGE    # e.g. a missing form field
    assert TextPrompt("> ").parse("  hello  ") == "hello"

# TextPrompt with a limit rejects long answers, without one, no message is built
def test_text_prompt_max_length():
    assert rejection(TextPrompt("> ", max_length=3), "abcdef") == "Please enter at most 3 characters."
    assert TextPrompt("> ", max_length=3).parse("abc") == "abc"
    assert TextPrompt("> ").too_long_msg is None

# RangePrompt rejects non-numbers, decimals for int, and out-of-range values
def test_range_prompt_int():
    prompt = RangePrompt("> ", 1, 10)
    assert rejection(prompt, "abc") == "Please enter a whole number."
    assert rejection(prompt, "5.5") == "Please enter a whole number."
    assert rejection(prompt, "11") == "Please enter a number from 1 to 10."
    assert prompt.parse("7") == 7
    assert prompt.parse(7) == 7
    assert rejection(prompt, 5.5) == "Please enter a whole number."
    assert rejection(prompt, True) == "Please enter a whole number."

# RangePrompt with cast=float accepts decimals and rejects nan
def test_range_prompt_float():
    prompt = RangePrompt("> ", 0, 24, cast=float)
    assert rejection(prompt, "nan") == "Please enter a number from 0 to 24."
    assert prompt.parse("7.5") == 7.5
    assert prompt.parse(8) == 8.0
    assert rejection(prompt, None) == "Please enter a valid number."

# ChoicePrompt returns the option itself, given its number or its name in any letter case
def test_choice_prompt():
    prompt = ChoicePrompt(["A", "B", "C"], "> ")
    assert prompt.parse("2") == "B"
    assert prompt.parse(" b ") == "B"
    assert rejection(prompt, "0") == "Please choose one of: A, B, C."
    assert rejection(prompt, "D") == "Please choose one of: A, B, C."

# ChoicePrompt needs at least one option
def test_choice_prompt_needs_options():
    with pytest.raises(ValueError):
        ChoicePrompt([], "> ")

# --- Questionnaire Tests ---

# from_answers() checks every answer and stores the user's id
def test_questionnaire_from_answers():
    response = Questionnaire().from_answers("123", {
        "sleep_duration": "7.5", "stress_level": "5", "focus_level": "6", "academic_workload": "4",
        "mood": "2", "social_activity_level": "3", "reflection": "Good week"})
    assert isinstance(response, SurveyResponse)
    assert response == SAMPLE_RESPONSE
    assert response.mood == "Calm" and response.sleep_duration == 7.5

# The chatbot's values (numbers, mood by name in any case) are accepted, other keys are ignored
def test_questionnaire_from_chatbot_values():
    answers = {**SAMPLE_ANSWERS, "mood": "calm", "text": "Thanks!", "survey_done": True}
    assert Questionnaire().from_answers("123", answers) == SAMPLE_RESPONSE

# Every invalid or missing answer is reported in question order, with the same messages as before
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

# from_answers() needs the user's id
def test_questionnaire_requires_user_id():
    with pytest.raises(TypeError):
        Questionnaire().from_answers(answers=SAMPLE_ANSWERS)

# --- Survey Response Tests ---

# to_dict() gives the same dictionary format as before (user_id first, then each question in order)
def test_survey_response_to_dict():
    assert SAMPLE_RESPONSE.to_dict() == {
        "user_id": "123", "sleep_duration": 7.5, "stress_level": 5, "focus_level": 6,
        "academic_workload": 4, "mood": "Calm", "social_activity_level": 3, "reflection": "Good week"}
    assert list(SAMPLE_RESPONSE.to_dict())[0] == "user_id"

# from_dict() and to_dict() round-trip; a missing answer is rejected
def test_survey_response_from_dict():
    assert SurveyResponse.from_dict(SAMPLE_RESPONSE.to_dict()) == SAMPLE_RESPONSE
    incomplete = SAMPLE_RESPONSE.to_dict()
    del incomplete["mood"]
    with pytest.raises(TypeError):
        SurveyResponse.from_dict(incomplete)

# /submit_survey builds a SurveyResponse from the user id plus the chatbot's answers, then hands it to
# LogicManager.assess(), which reads its attributes. Fails if the chatbot's field names stop matching SurveyResponse's
def test_survey_response_from_chatbot_answers():
    from types import SimpleNamespace
    from ai_manager_helper.data_classes.survey_entity_schema import SurveyEntitySchema
    from logic_manager_helper.LogicManager import LogicManager
    answers = SurveyEntitySchema(**{"Sleep duration": 7, "Stress level": 5, "focus_level": 6, "academic_workload": 4,
                                    "mood": "Calm", "social_activity_level": 3, "reflection": "Good week",
                                    "text": "Done!", "survey_done": True})
    del answers.text, answers.survey_done      # as ai_manager.show_survey_results() does

    response = SurveyResponse(**{"user_id": "123", **answers.model_dump()})     # as app.py's /submit_survey does
    ai_output = SimpleNamespace(mental_wellness_risk_score=40, burnout_risk_score=50, sentiment="Neutral", crisis_alert=False)
    assert response == SurveyResponse("123", 7, 5, 6, 4, "Calm", 3, "Good week")
    assert LogicManager().assess(response, ai_output, []).route

# Check that heading turns a key into a title
def test_questionnaire_heading():
    assert Questionnaire.heading("social_activity_level") == "Social Activity Level"

# --- Account Service Tests ---

# Stand-in for DataManager's user methods, behaving like UserManager + MongoDBStorage:
class FakeUserData:
    def __init__(self):
        self.users = []
        self.fail_saves = False    # set True to act like a MongoDB error

    def get_users(self):
        return self.users.copy()

    def get_user_by_id(self, user_id):
        return next((u for u in self.users if u.get_user_id() == user_id), None)

    def get_user_by_username(self, username):
        return next((u for u in self.users if u.get_username() == username), None)

    def _taken(self, username, uid=None):
        return any(u.get_username() == username and u.get_user_id() != uid for u in self.users)

    def create_user(self, username, password):
        if self.fail_saves or self._taken(username):
            print("Error: A record with the same unique value already exists.")
            return None
        user = UserRecord(username, password)
        self.users.append(user)
        return user.get_user_id()

    def update_user(self, user_id, updates):
        user = self.get_user_by_id(user_id)
        if self.fail_saves or ("username" in updates and self._taken(updates["username"], user_id)):
            print("Error: Update violates a unique field constraint.")
            return False
        data = {**user.to_dict(), **updates}
        self.users[self.users.index(user)] = UserRecord(data["username"], data["password"], user_id)
        return True


# AccountService with a fake DataManager and a fast hasher
def make_accounts():
    return AccountService(FakeUserData(), PasswordHasher(iterations=1000))

# Register, then log in with the same details passed as parameters (password stored hashed, not plain)
def test_register_and_login():
    accounts = make_accounts()
    registered = accounts.register("Alice", "pass1!", "pass1!")
    assert registered.ok and registered.username == "alice"
    stored = accounts.data.get_users()[0]
    assert stored.get_username() == "alice"
    assert stored.get_password() != "pass1!"

    logged_in = accounts.login("ALICE", "pass1!")
    assert logged_in.ok and logged_in.uid == registered.uid
    assert logged_in.message == "Login successful! Welcome, alice!"

# Failed account actions return ok=False with the web pages' messages
def test_account_failures():
    accounts = make_accounts()
    assert accounts.login("Alice", "pass1!").message == "No users registered yet. Please register first."
    accounts.register("Alice", "pass1!", "pass1!")
    assert accounts.register("ALICE", "pass1!", "pass1!").message == "This username already exists. Please choose another."
    assert accounts.register("Bob", "pass1!", "other1!").message == "Passwords do not match."
    assert accounts.login("Alice", "wrong1!").message == "Invalid username or password."
    assert accounts.login("Nobody", "pass1!").message == "Invalid username or password."

# Register checks in the same order as before and stops at the first problem
def test_register_check_order():
    accounts = make_accounts()
    assert accounts.register("ab", "x", "y").message == USERNAME_RULES    # username rules first
    accounts.register("Alice", "pass1!", "pass1!")
    assert accounts.register("alice", "x", "y").message == "This username already exists. Please choose another."
    assert accounts.register("Bob", "abcd", "y").message == \
        "at least one number at least one special character (e.g. ! @ # $ %)"    # then the password rules
    assert accounts.register("Bob", "pass1!", "").message == "Passwords do not match."    # then the confirmation
    assert len(accounts.data.get_users()) == 1

# Answers are trimmed and missing answers (None) count as empty
def test_account_answers_trimmed_or_missing():
    accounts = make_accounts()
    assert accounts.register("  Alice  ", " pass1! ", "pass1!").ok
    assert accounts.data.get_users()[0].get_username() == "alice"
    assert accounts.login(" alice ", "pass1! ").ok
    assert accounts.register(None, None, None).message == USERNAME_RULES
    assert accounts.register("Bob", None, None).message == PASSWORD_RULES_ALL
    assert accounts.login(None, None).message == "Invalid username or password."

# Usernames match in any letter case, so accounts saved with capitals (e.g. by the old web pages) still log in
def test_login_ignores_case_for_existing_accounts():
    accounts = make_accounts()
    accounts.data.users.append(UserRecord("Marcus", PasswordHasher(iterations=1000).hash("pass1!")))
    assert accounts.login("marcus", "pass1!").ok
    assert accounts.login("MARCUS", "pass1!").username == "Marcus"
    assert accounts.register("marcus", "pass1!", "pass1!").message == "This username already exists. Please choose another."

# When accounts differ only in letter case, an exact match wins, then the lowercase one
def test_login_prefers_exact_then_lowercase():
    hasher = PasswordHasher(iterations=1000)
    accounts = make_accounts()
    accounts.data.users += [UserRecord("Alice", hasher.hash("upper1!")), UserRecord("alice", hasher.hash("lower1!"))]
    assert accounts.login("Alice", "upper1!").username == "Alice"
    assert accounts.login("alice", "lower1!").username == "alice"
    assert accounts.login("ALICE", "lower1!").username == "alice"

# Change username (taken names rejected in any case) and change password, given as parameters
def test_change_username_and_password():
    accounts = make_accounts()
    uid = accounts.register("Alice", "pass1!", "pass1!").uid
    accounts.register("Bob", "pass1!", "pass1!")
    assert accounts.change_username(uid, "BOB").message == "This username already exists. Please choose another."
    changed = accounts.change_username(uid, "Carol")
    assert changed.ok and changed.username == "carol"
    assert changed.message == "Your username has been successfully updated!"
    assert accounts.data.get_user_by_id(uid).get_username() == "carol"
    assert accounts.change_password(uid, "wrong1!", "new2@", "new2@").message == "Incorrect password. Please try again."
    changed = accounts.change_password(uid, "pass1!", "new2@", "new2@")
    assert changed.ok and changed.message == "Your password has been successfully updated!"
    assert accounts.login("Carol", "new2@").ok

# Changes use the register rules, checked in the same order as before
def test_change_checks():
    accounts = make_accounts()
    uid = accounts.register("Alice", "pass1!", "pass1!").uid
    assert accounts.change_username(uid, "  ").message == "Please Enter a username"
    assert accounts.change_username(uid, "x!").message == USERNAME_RULES
    assert accounts.change_username(uid, "ALICE").ok    # the user's own name is harmless
    assert accounts.change_password(uid, "", "new2@", "new2@").message == "Please enter your old password"
    assert accounts.change_password(uid, "pass1!", "", "").message == "Please enter your new password"
    assert accounts.change_password(uid, "pass1!", "a", "a").message == PASSWORD_RULES_ALL
    assert accounts.change_password(uid, "pass1!", "new2@", "").message == "Please confirm your new password"
    assert accounts.change_password(uid, "pass1!", "new2@", "new3@").message == "Your new password & confirmation do not match."
    assert accounts.login("alice", "pass1!").ok    # the password was never changed

# An unknown user id or a failed save is reported instead of crashing
def test_unknown_user_and_failed_saves():
    accounts = make_accounts()
    assert accounts.change_username("nope", "carol").message == "Current user not found."
    assert accounts.change_password("nope", "pass1!", "new2@", "new2@").message == "Current user not found."
    assert accounts.get_username("nope") is None
    uid = accounts.register("Alice", "pass1!", "pass1!").uid
    assert accounts.get_username(uid) == "alice"

    accounts.data.fail_saves = True
    assert accounts.register("Bob", "pass1!", "pass1!").message == "Could not create your account. Please try again."
    assert accounts.change_username(uid, "carol").message == "There was an error with updating your username. Please try again."
    assert accounts.change_password(uid, "pass1!", "new2@", "new2@").message == "There has been an issue with updating your password. Please try again later"

# A database connection error while registering gives the register page's message
def test_register_connection_error():
    accounts = make_accounts()
    accounts.data.create_user = MagicMock(side_effect=ConnectionError("down"))
    assert accounts.register("Alice", "pass1!", "pass1!").message == "Unable to connect to the database. Please try again later."

# Account actions also accept their answers by name
def test_account_actions_keyword_arguments():
    accounts = make_accounts()
    uid = accounts.register(username="Alice", password="pass1!", confirm="pass1!").uid
    assert accounts.change_password(uid=uid, current_password="pass1!", new_password="new2@", confirm="new2@").ok

# IOManager builds its AccountService in __init__, with the same DataManager
def test_accounts_share_data_manager():
    data = fake_data()
    app = IOManager(data=data)
    assert app.data is data
    assert app.accounts.data is data

# --- Trends Tests ---

# With fewer than 2 records there is no trend data
def test_trends_not_enough_records():
    data = fake_data([fake_record()])
    assert trend_points(data, "123") is None
    data.get_user_int_records.assert_not_called()
    assert MIN_RECORDS == 2

# With 2+ records, the data comes from get_user_int_records(), oldest -> newest
def test_trends_oldest_first():
    records = [fake_record("02-01-2026"), fake_record("01-01-2026")]
    data = fake_data(records)
    data.get_user_int_records.return_value = [{"date": "02-01-2026"}, {"date": "01-01-2026"}]
    assert IOManager(data).trends("123") == [{"date": "01-01-2026"}, {"date": "02-01-2026"}]
    data.get_user_int_records.assert_called_once_with(records, "123")