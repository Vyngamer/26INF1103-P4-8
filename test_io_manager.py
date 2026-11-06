from unittest.mock import patch, MagicMock
import pytest
from io_manager import (IOManager, AssessmentHistory, YesNoPrompt, Questionnaire)
from io_helpers.console import Console
from io_helpers.session import Session
from io_helpers.account_models import AccountResult
from io_helpers.account_models import User, AccountError
from io_helpers.account_service import AccountService
from io_helpers.user_repository import UserRepository
from io_helpers.hasher import PasswordHasher
from io_helpers.validators import username_errors, password_errors, USERNAME_RULES
from io_helpers.prompts import TextPrompt, RangePrompt, ChoicePrompt
from io_helpers.trends import show_trends
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
@patch.object(AssessmentHistory, 'todays_records', return_value=[{'time': '10:00:00', 'record_id': 'abc'}])
@patch.object(Console, 'pause')
def test_survey_existing_record_kept(mock_pause, mock_todays_records, mock_yes_no, capsys):
    result = IOManager().collect_responses("test_uuid")

    captured = capsys.readouterr()
    assert result is None
    assert "You have already completed an assessment today" in captured.out
    assert "Your existing assessment for today has been kept." in captured.out
    mock_pause.assert_called_once()

# With no existing assessment today, the questionnaire runs straight away
@patch.object(Questionnaire, 'run', return_value={"user_id": None, "mood": "Calm"})
@patch.object(AssessmentHistory, 'todays_records', return_value=[])
def test_survey_runs_questionnaire_when_none_today(mock_todays_records, mock_run):
    result = IOManager().collect_responses("test_uuid")

    assert result == {"user_id": None, "mood": "Calm"}
    mock_run.assert_called_once_with("test_uuid")

# survey() hands the answers to the process_responses function given to IOManager
@patch.object(Questionnaire, 'run', return_value={"user_id": None, "mood": "Calm"})
@patch.object(AssessmentHistory, 'todays_records', return_value=[])
def test_survey_passes_responses_to_function(mock_todays_records, mock_run):
    received = []
    app = IOManager(process_responses=lambda session, responses: received.append((session.uid, responses)))
    app.session.log_in("123", "test")
    app.survey()

    assert received == [("123", {"user_id": None, "mood": "Calm"})]

# Check that survey() still runs without errors when no process_responses function is provided
@patch.object(Questionnaire, 'run', return_value={"user_id": None, "mood": "Calm"})
@patch.object(AssessmentHistory, 'todays_records', return_value=[])
def test_survey_without_function(mock_todays_records, mock_run):
    app = IOManager()
    app.session.log_in("123", "test")
    app.survey()
    mock_run.assert_called_once()

# --- History Tests ---

# Check that history() prints a message and returns without showing a menu when there are no records
@patch.object(AssessmentHistory, 'records', return_value=[])
def test_history_no_records(mock_records, capsys):
    app = IOManager()
    app.session.log_in("123", "test")
    app.history()
    assert "No assessment history found." in capsys.readouterr().out

# Check that choosing "Back" in the history sub-menu leaves history()
@patch('io_manager.AssessmentHistoryTable')
@patch.object(AssessmentHistory, 'records', return_value=[{"dummy": True}])
@patch('builtins.input', return_value="2")    # option 2 = Back
def test_history_back(mock_input, mock_records, mock_table):
    app = IOManager()
    app.session.log_in("123", "test")
    app.history()
    mock_table.assert_called_once_with([{"dummy": True}])

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
    assert Questionnaire().run("123") == {
        "user_id": "123", "sleep_duration": 7.5, "stress_level": 5, "focus_level": 6,
        "academic_workload": 4, "mood": "Calm", "social_activity_level": 3, "reflection": "Good week"}

# Check that Ctrl+C during the survey cancels it and returns None
@patch('builtins.input', side_effect=KeyboardInterrupt)
def test_questionnaire_cancelled(mock_input, capsys):
    assert Questionnaire().run("123") is None
    assert "Survey cancelled." in capsys.readouterr().out

# Check that heading turns a key into a title
def test_questionnaire_heading():
    assert Questionnaire.heading("social_activity_level") == "Social Activity Level"

# --- User Repository Tests ---

# Check that save then load gives back the same users; a missing file loads as []
def test_repository_save_and_load(tmp_path):
    repo = UserRepository(str(tmp_path / "users.json"))
    assert repo.load() == []
    users = [User("1", "Alice", "hash")]
    repo.save(users)
    assert repo.load() == users

# Check that every kind of damaged users.json gives the "corrupted" AccountError instead of crashing
@pytest.mark.parametrize("content", [b"{not json", b'{"user_id": "1"}', b'[{"user_id": "1"}]', b"\xff\xfe\x00"])
def test_repository_corrupted_file(tmp_path, content):
    path = tmp_path / "users.json"
    path.write_bytes(content)
    with pytest.raises(AccountError, match="corrupted"):
        UserRepository(str(path)).load()

# Check that username lookup ignores case; id lookup is exact
def test_repository_find():
    users = [User("1", "Alice", "h"), User("2", "Bob", "h")]
    assert UserRepository.find_by_username(users, "aLiCe") is users[0]
    assert UserRepository.find_by_username(users, "Carol") is None
    assert UserRepository.find_by_id(users, "2") is users[1]
    assert UserRepository.find_by_id(users, "3") is None

# --- Account Service Tests ---

# Test that AccountService using a temp users file and a fast hasher works correctly
def make_accounts(tmp_path):
    return AccountService(UserRepository(str(tmp_path / "users.json")), PasswordHasher(iterations=1000))

# Test for register, then log in with the same details (password stored hashed, not plain)
def test_register_and_login(tmp_path):
    accounts = make_accounts(tmp_path)
    with patch('builtins.input', side_effect=["Alice", "pass1!", "pass1!"]):
        registered = accounts.register()
    assert registered.ok and registered.username == "Alice"
    assert accounts.repository.load()[0].password != "pass1!"

    with patch('builtins.input', side_effect=["alice", "pass1!"]):
        logged_in = accounts.login()
    assert logged_in.ok and logged_in.uid == registered.uid

# Test that failed account actions return ok=False with the right message
def test_account_failures(tmp_path):
    accounts = make_accounts(tmp_path)
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

# Test to change username (own name in a new case is allowed) and change password
def test_change_username_and_password(tmp_path):
    accounts = make_accounts(tmp_path)
    with patch('builtins.input', side_effect=["Alice", "pass1!", "pass1!"]):
        uid = accounts.register().uid
    with patch('builtins.input', side_effect=["ALICE"]):
        assert accounts.change_username(uid).username == "ALICE"
    with patch('builtins.input', side_effect=["wrong1!"]):
        assert accounts.change_password(uid).message == "Incorrect current password. Please try again."
    with patch('builtins.input', side_effect=["pass1!", "new2@", "new2@"]):
        assert accounts.change_password(uid).ok
    with patch('builtins.input', side_effect=["ALICE", "new2@"]):
        assert accounts.login().ok

# --- Trends Tests ---

# Test that with fewer than 2 records, no graph is drawn
@patch.object(Console, 'pause')
@patch('io_helpers.trends.get_user_records', return_value=[{"only": "one"}])
def test_trends_not_enough_records(mock_records, mock_pause, capsys):
    show_trends("123", "records.json")
    assert "You do not have enough records" in capsys.readouterr().out
    mock_pause.assert_called_once()