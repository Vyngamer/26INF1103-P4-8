from unittest.mock import patch, MagicMock
import pytest
from io_manager import (IOManager, YesNoPrompt, Questionnaire, main) 
from pymongo.errors import ConfigurationError
from io_helpers.history import todays_records, AssessmentHistoryTable, AssessmentDetailView
from io_helpers.console import Console
from io_helpers.session import Session
from io_helpers.account_models import AccountResult
from io_helpers.account_service import AccountService
from data_manager_helper.UserRecord import UserRecord
from io_helpers.hasher import PasswordHasher
from io_helpers.validators import username_errors, password_errors, USERNAME_RULES
from io_helpers.prompts import TextPrompt, RangePrompt, ChoicePrompt
from io_helpers.trends import show_trends
from io_helpers.survey_response import SurveyResponse

# Sample completed survey, used by the survey tests below
SAMPLE_RESPONSE = SurveyResponse("123", 7.5, 5, 6, 4, "Calm", 3, "Good week")


# Mock data manager so that test do not create a real DataManager (that would connect to MongoDB Atlas).
@pytest.fixture(autouse=True)
def no_real_database():
    with patch('io_manager.DataManager') as mock_data_manager:
        yield mock_data_manager

def fake_record(date="01-01-2026", time="10:00:00"):
    record = MagicMock()
    record.get_date.return_value = date
    record.get_time.return_value = time
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

# --- Session Tests ---

#Test that a fresh session initializes correctly
def test_new_session():
    session = Session()
    assert session.running is True
    assert session.uid is None
    assert session.username is None

#Test that a user's ID and username are properly saved to the session
def test_log_in():
    session = Session()
    session.log_in("test_uuid_123", "test_user")

    assert session.uid == "test_uuid_123"
    assert session.username == "test_user"
    assert session.running is True

#Test the boolean check for user login status
def test_is_logged_in():
    session = Session()
    assert not session.is_logged_in()

    session.log_in("test_uuid_123", "test_user")
    assert session.is_logged_in()

#Test that logging out correctly clears the user data but keeps the app running
def test_log_out():
    session = Session()
    session.log_in("test_uuid_123", "test_user")
    session.log_out()

    assert session.uid is None
    assert session.username is None
    assert session.running is True

# --- Display Output Tests ---

#Test standard error output format
def test_console_error(capsys):
    Console.error("Invalid input")
    captured = capsys.readouterr()
    assert captured.out == "\nERROR: Invalid input\n"

#Test the standard notice output format
def test_console_notice(capsys):
    Console.notice("Action successful")
    captured = capsys.readouterr()
    assert captured.out == "\nNOTICE: Action successful\n"

#Test the standard welcome output format
def test_console_welcome(capsys):
    Console.welcome("Main Menu")
    captured = capsys.readouterr()
    assert captured.out == "\n---Main Menu---\n"

#Test the exit message output
def test_console_termination_msg(capsys):
    Console.termination_msg()
    captured = capsys.readouterr()
    assert captured.out == "\n\nProgram terminated. Thank You!\n"

# --- Menu Tests ---

#Test that the correct menu is returned based on login state
def test_current_menu():
    app = IOManager()

    #When logged out, should return the main menu
    assert app.current_menu() is app.main_menu

    #When logged in, should return the user menu
    app.session.log_in("123", "test")
    assert app.current_menu() is app.user_menu

# Check each menu lists the right options, in the right order
def test_menu_labels():
    app = IOManager()
    assert [label for label, _ in app.main_menu] == ["Register New User", "Login", "Exit"]
    assert [label for label, _ in app.user_menu] == [
        "Start Survey", "View History", "Change Username",
        "Change Password", "View Assessment Trends", "Logout"]

# Check that choose() returns the method for the chosen option
@patch('builtins.input', return_value="2")
def test_choose_returns_method(mock_input):
    app = IOManager()
    assert app.choose(app.main_menu) == app.login

# Check that choose() returns None for the "Back" option
@patch('builtins.input', return_value="2")
def test_choose_back_returns_none(mock_input):
    app = IOManager()
    assert app.choose([("Something", app.logout), ("Back", None)]) is None

# --- Action Tests ---

#Test that logout updates the session and prints success message
def test_logout(capsys):
    app = IOManager()
    app.session.log_in("123", "test")
    app.logout()

    captured = capsys.readouterr()
    assert app.session.uid is None
    assert app.session.username is None
    assert "\nSuccessfully Logged Out.\n" in captured.out

#Test that exit flags the session as not running (which ends IOManager.run's loop)
def test_exit(capsys):
    app = IOManager()
    app.exit()

    captured = capsys.readouterr()
    assert app.session.running is False
    assert "\nProgram terminated. Thank You!\n" in captured.out

# Checks that a successful login stores the user in the session
def test_login_success(capsys):
    accounts = MagicMock()
    accounts.login.return_value = AccountResult(True, "Login successful! Welcome, test!",
                                                uid="123", username="test")
    app = IOManager(accounts=accounts)
    app.login()

    assert app.session.uid == "123"
    assert app.session.username == "test"
    assert "Login successful! Welcome, test!" in capsys.readouterr().out

# Checks that a failed login leaves the session logged out
def test_login_failure(capsys):
    accounts = MagicMock()
    accounts.login.return_value = AccountResult(False, "Invalid username or password.")
    app = IOManager(accounts=accounts)
    app.login()

    assert not app.session.is_logged_in()
    assert "Invalid username or password." in capsys.readouterr().out

# Check that run() keeps choosing and running menu options until exit stops the loop
@patch('builtins.input', return_value="3")    # option 3 on the main menu = Exit
def test_run_until_exit(mock_input, capsys):
    app = IOManager()
    app.run()

    assert app.session.running is False
    assert "Program terminated. Thank You!" in capsys.readouterr().out

# --- Survey Tests ---

#Test that a user with an existing survey today is prevented from overwriting if they say 'no'
@patch.object(YesNoPrompt, 'ask', return_value=False)
@patch('io_manager.todays_records', return_value=[fake_record(time="10:00:00")])
@patch.object(Console, 'pause')
def test_survey_existing_record_kept(mock_pause, mock_todays_records, mock_yes_no, capsys):
    data = fake_data()
    result = IOManager(data=data).collect_responses("test_uuid")

    captured = capsys.readouterr()
    assert result is None
    mock_todays_records.assert_called_once_with(data, "test_uuid")
    assert "You have already completed an assessment today (at 10:00:00)" in captured.out
    assert "Your existing assessment for today has been kept." in captured.out
    mock_pause.assert_called_once()

# Ctrl+C at the "replace today's assessment?" question keeps today's assessment instead of quitting
@patch.object(Questionnaire, 'run')
@patch('io_manager.todays_records', return_value=[fake_record()])
@patch.object(Console, 'pause')
@patch('builtins.input', side_effect=KeyboardInterrupt)
def test_survey_ctrl_c_at_replace_question(mock_input, mock_pause, mock_todays_records, mock_run, capsys):
    assert IOManager(data=fake_data()).collect_responses("test_uuid") is None
    assert "Your existing assessment for today has been kept." in capsys.readouterr().out
    mock_run.assert_not_called()

# With no existing assessment today, the questionnaire runs straight away
@patch.object(Questionnaire, 'run', return_value=SAMPLE_RESPONSE)
@patch('io_manager.todays_records', return_value=[])
def test_survey_runs_questionnaire_when_none_today(mock_todays_records, mock_run):
    result = IOManager().collect_responses("test_uuid")

    assert result is SAMPLE_RESPONSE
    mock_run.assert_called_once_with("test_uuid")

# survey() hands the answers to the process_responses function given to IOManager
@patch.object(Questionnaire, 'run', return_value=SAMPLE_RESPONSE)
@patch('io_manager.todays_records', return_value=[])
def test_survey_passes_responses_to_function(mock_todays_records, mock_run):
    received = []
    app = IOManager(process_responses=lambda session, responses: received.append((session.uid, responses)))
    app.session.log_in("123", "test")
    app.survey()

    assert received == [("123", SAMPLE_RESPONSE)]

# Check that survey() still runs without errors when no process_responses function is provided
@patch.object(Questionnaire, 'run', return_value=SAMPLE_RESPONSE)
@patch('io_manager.todays_records', return_value=[]) 
def test_survey_without_function(mock_todays_records, mock_run):
    app = IOManager()
    app.session.log_in("123", "test")
    app.survey()
    mock_run.assert_called_once()

# --- History Tests ---

# Check that history() prints a message and returns without showing a menu when there are no records
def test_history_no_records(capsys):
    app = IOManager(data=fake_data([]))
    app.session.log_in("123", "test")
    app.history()
    assert "No assessment history found." in capsys.readouterr().out

# Check that choosing "Back" in the history sub-menu leaves history()
@patch('io_manager.AssessmentHistoryTable')
@patch('builtins.input', return_value="2")    # option 2 = Back
def test_history_back(mock_input, mock_table):
    record = fake_record()
    data = fake_data([record])
    app = IOManager(data=data)
    app.session.log_in("123", "test")
    app.history()
    data.get_user_records.assert_called_once_with("123")
    mock_table.assert_called_once_with([record])

# Check that history_details() shows the record with the chosen No. (1 = first row of the table)
@patch('io_manager.AssessmentDetailView')
@patch.object(Console, 'pause')
@patch('builtins.input', return_value="2")
def test_history_details_shows_chosen_record(mock_input, mock_pause, mock_view):
    records = [fake_record(time="15:00:00"), fake_record(time="10:00:00")]
    app = IOManager(data=fake_data(records))
    app.session.log_in("123", "test")
    app.history_details()
    mock_view.assert_called_once_with(records[1])

# Check that todays_records() keeps only records dated today, in the same (newest first) order
def test_todays_records():
    from datetime import datetime
    today = datetime.now().strftime("%d-%m-%Y")
    records = [fake_record(today, "15:00:00"), fake_record("01-01-2000", "09:00:00"), fake_record(today, "10:00:00")]
    data = fake_data(records)
    assert todays_records(data, "123") == [records[0], records[2]]
    data.get_user_records.assert_called_once_with("123")

# Check that the history table reads each record through its getters
def test_history_table_shows_records(capsys):
    AssessmentHistoryTable([fake_record("02-01-2026", "09:30:00")]).show()
    out = capsys.readouterr().out
    assert "02-01-2026" in out and "09:30:00" in out and "Moderate" in out and "Calm" in out
    assert "Total assessments: 1" in out

# Check that the detail view reads the record through its getters
def test_detail_view_shows_record(capsys):
    AssessmentDetailView(fake_record("02-01-2026", "09:30:00")).show()
    out = capsys.readouterr().out
    assert "Date      : 02-01-2026" in out
    assert "Sleep Duration       : 7.5 hours" in out
    assert "Primary Stressor     : Exams" in out
    assert "Counselling Required : No" in out

# --- DataManager Sharing Tests ---

# Check that a DataManager passed in is used as-is, and no new one is created
def test_uses_given_data_manager(no_real_database):
    data = fake_data()
    assert IOManager(data=data).data is data
    no_real_database.assert_not_called()

# Check that one DataManager is created on first use and then reused
def test_creates_one_data_manager_when_needed(no_real_database):
    app = IOManager()
    no_real_database.assert_not_called()    # not connected just by creating the IOManager
    assert app.data is app.data
    no_real_database.assert_called_once()

# --- Startup Tests (main) ---

# Check that very kind of connection failure gives one clear error and the menu never starts.
# ConfigurationError is what pymongo raises for a mongodb+srv:// address with no internet
@pytest.mark.parametrize("error", [ConnectionError("Unable to connect to MongoDB Atlas."),
                                   ValueError("MONGODB_URI is not configured in the .env file."),
                                   ConfigurationError("The DNS query name does not exist")])
@patch.object(IOManager, 'run')
def test_main_connection_errors(mock_run, no_real_database, error, capsys):
    no_real_database.side_effect = error
    main()
    assert f"ERROR: Could not open the database: {error}" in capsys.readouterr().out
    mock_run.assert_not_called()

# Check that connection is made at startup, before the first menu, and closed on exit
def test_main_connects_before_menu(no_real_database, capsys):
    def first_input(prompt):
        assert no_real_database.called    # already connected when the menu asks for input
        return "3"                        # Exit
    with patch('builtins.input', side_effect=first_input):
        main()
    no_real_database.return_value.close.assert_called_once()
    assert "Program terminated. Thank You!" in capsys.readouterr().out

# Check that an error later in the session is not reported as a database error
# and the connection is still closed
@patch.object(IOManager, 'run', side_effect=ValueError("some other bug"))
def test_main_does_not_hide_other_errors(mock_run, no_real_database, capsys):
    with pytest.raises(ValueError, match="some other bug"):
        main()
    assert "Could not open the database" not in capsys.readouterr().out
    no_real_database.return_value.close.assert_called_once()

# Check that Ctrl+C while connecting, or during the menu, ends the program politely
@pytest.mark.parametrize("while_connecting", [True, False])
@patch('builtins.input', side_effect=KeyboardInterrupt)
def test_main_ctrl_c(mock_input, no_real_database, while_connecting, capsys):
    if while_connecting:
        no_real_database.side_effect = KeyboardInterrupt
    main()
    assert "Program terminated. Thank You!" in capsys.readouterr().out
    if not while_connecting:
        no_real_database.return_value.close.assert_called_once()

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

# Check that TextPrompt re-asks on empty input and trims whitespace
@patch('builtins.input', side_effect=["", "  hello  "])
def test_text_prompt(mock_input, capsys):
    assert TextPrompt("> ").ask() == "hello"
    assert TextPrompt.EMPTY_MESSAGE in capsys.readouterr().out

# Check that TextPrompt with a limit rejects long answers; without one, no message is built
@patch('builtins.input', side_effect=["abcdef", "abc"])
def test_text_prompt_max_length(mock_input, capsys):
    assert TextPrompt("> ", max_length=3).ask() == "abc"
    assert "Please enter at most 3 characters." in capsys.readouterr().out
    assert TextPrompt("> ").too_long_msg is None

# Check that RangePrompt rejects non-numbers, decimals for int, and out-of-range values
@patch('builtins.input', side_effect=["abc", "5.5", "11", "7"])
def test_range_prompt_int(mock_input, capsys):
    assert RangePrompt("> ", 1, 10).ask() == 7
    out = capsys.readouterr().out
    assert "Please enter a whole number." in out
    assert "Please enter a number from 1 to 10." in out

# Check that RangePrompt with cast=float accepts decimals and rejects nan
@patch('builtins.input', side_effect=["nan", "7.5"])
def test_range_prompt_float(mock_input):
    assert RangePrompt("> ", 0, 24, cast=float).ask() == 7.5

# Check that ChoicePrompt returns the option itself, not its number
@patch('builtins.input', side_effect=["0", "2"])
def test_choice_prompt(mock_input):
    assert ChoicePrompt(["A", "B", "C"], "Pick:", "> ").ask() == "B"

# Check that YesNoPrompt accepts y/yes/n/no in any case and re-asks otherwise
@patch('builtins.input', side_effect=["maybe", "YES", "n"])
def test_yes_no_prompt(mock_input):
    assert YesNoPrompt("> ").ask() is True
    assert YesNoPrompt("> ").ask() is False

# --- Questionnaire Tests ---

# Check that run() asks every question in order and stores the user's id
@patch('builtins.input', side_effect=["7.5", "5", "6", "4", "2", "3", "Good week"])
def test_questionnaire_run(mock_input):
    response = Questionnaire().run("123")
    assert isinstance(response, SurveyResponse)
    assert response == SAMPLE_RESPONSE
    assert response.mood == "Calm" and response.sleep_duration == 7.5

# Check that the questions match SurveyResponse's corresponding fields exactly
def test_questions_match_survey_response():
    from dataclasses import fields
    assert [key for key, _ in Questionnaire().questions] == [f.name for f in fields(SurveyResponse)][1:]

# questionnaire.run() needs the user's id
def test_questionnaire_run_requires_user_id():
    with pytest.raises(TypeError):
        Questionnaire().run()

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

# Check that Ctrl+C during the survey cancels it and returns None
@patch('builtins.input', side_effect=KeyboardInterrupt)
def test_questionnaire_cancelled(mock_input, capsys):
    assert Questionnaire().run("123") is None
    assert "Survey cancelled." in capsys.readouterr().out

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

# Test for register, then log in with the same details (password stored hashed, not plain)
def test_register_and_login():
    accounts = make_accounts()
    with patch('builtins.input', side_effect=["Alice", "pass1!", "pass1!"]):
        registered = accounts.register()
    assert registered.ok and registered.username == "alice"
    stored = accounts.data.get_users()[0]
    assert stored.get_username() == "alice"
    assert stored.get_password() != "pass1!"

    with patch('builtins.input', side_effect=["ALICE", "pass1!"]):
        logged_in = accounts.login()
    assert logged_in.ok and logged_in.uid == registered.uid
    assert logged_in.message == "Login successful! Welcome, alice!"

# Test that failed account actions return ok=False with the right message
def test_account_failures():
    accounts = make_accounts()
    with patch('builtins.input', side_effect=[]):
        assert accounts.login().message == "No users registered yet. Please register first."
    with patch('builtins.input', side_effect=["Alice", "pass1!", "pass1!"]):
        accounts.register()
    with patch('builtins.input', side_effect=["ALICE"]):
        assert accounts.register().message == "Username already exists, please try again."
    with patch('builtins.input', side_effect=["Bob", "pass1!", "other1!"]):
        assert accounts.register().message == "Passwords do not match, please try again."
    with patch('builtins.input', side_effect=["Alice", "wrong1!"]):
        assert accounts.login().message == "Invalid username or password."

# Test to change username (taken names rejected in any case) and change password
def test_change_username_and_password():
    accounts = make_accounts()
    with patch('builtins.input', side_effect=["Alice", "pass1!", "pass1!"]):
        uid = accounts.register().uid
    with patch('builtins.input', side_effect=["Bob", "pass1!", "pass1!"]):
        accounts.register()
    with patch('builtins.input', side_effect=["BOB"]):
        assert accounts.change_username(uid).message == "Username already exists, please try again."
    with patch('builtins.input', side_effect=["Carol"]):
        assert accounts.change_username(uid).username == "carol"
    assert accounts.data.get_user_by_id(uid).get_username() == "carol"
    with patch('builtins.input', side_effect=["wrong1!"]):
        assert accounts.change_password(uid).message == "Incorrect current password. Please try again."
    with patch('builtins.input', side_effect=["pass1!", "new2@", "new2@"]):
        assert accounts.change_password(uid).ok
    with patch('builtins.input', side_effect=["Carol", "new2@"]):
        assert accounts.login().ok

# IOManager builds its AccountService on first use, with the same DataManager
def test_accounts_share_data_manager():
    data = fake_data()
    app = IOManager(data=data)
    assert app.accounts.data is data
    assert app.accounts is app.accounts

# --- Trends Tests ---

# Test that with fewer than 2 records, no graph is drawn
@patch.object(Console, 'pause')
def test_trends_not_enough_records(mock_pause, capsys):
    data = fake_data([fake_record()])
    show_trends(data, "123")
    assert "You do not have enough records" in capsys.readouterr().out
    mock_pause.assert_called_once()
    data.get_user_int_records.assert_not_called()

# With 2+ records, the graph uses get_user_int_records() and is saved to the output file
@patch('io_helpers.trends.can_show_window', return_value=False)
@patch.object(Console, 'pause')
def test_trends_saves_graph(mock_pause, mock_window, tmp_path):
    records = [fake_record(), fake_record()]
    data = fake_data(records)
    data.get_user_int_records.return_value = [
        {"sleep_duration": 7, "focus_level": 6, "stress_level": 5, "social_activity_level": 4,
         "mental_wellness_risk_score": 40, "burnout_risk_score": 50}] * 2
    output = tmp_path / "graph.png"
    show_trends(data, "123", output_file=str(output))
    data.get_user_int_records.assert_called_once_with(records, "123")
    assert output.exists()