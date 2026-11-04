from unittest.mock import patch, MagicMock
from io_manager import (Session, WellbeingApp, Menu, SurveyAction, LoginAction,
                        LogoutAction, ExitAction, BackAction, AssessmentHistory,
                        YesNoPrompt, Questionnaire)
from console import Console
from user import AccountResult

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
    app = WellbeingApp()

    #When logged out, should return the main menu
    assert app.current_menu() is app.main_menu

    #When logged in, should return the user menu
    app.session.log_in("123", "test")
    assert app.current_menu() is app.user_menu

# Check each menu lists the right options, in the right order
def test_menu_labels():
    app = WellbeingApp()
    assert [str(action) for action in app.main_menu.actions] == ["Register New User", "Login", "Exit"]
    assert [str(action) for action in app.user_menu.actions] == [
        "Start Survey", "View History", "Change Username",
        "Change Password", "View Assessment Trends", "Logout"]

# [OOP] NEW: main.py passes in its own survey action - it must replace the default one
def test_app_uses_given_survey_action():
    custom = SurveyAction()
    app = WellbeingApp(survey_action=custom)
    assert app.user_menu.actions[0] is custom

# Menu.choose() returns the chosen action object itself
@patch('builtins.input', return_value="2")
def test_menu_choose_returns_action(mock_input):
    login, logout = LoginAction(), LogoutAction()
    assert Menu([login, logout]).choose() is logout

# Only the Back action tells a sub-menu to close
def test_back_action_closes_menu():
    assert BackAction().closes_menu is True
    assert LogoutAction().closes_menu is False

# --- Action Tests ---

#Test that the logout action updates the session and prints success message
def test_logout_action(capsys):
    session = Session()
    session.log_in("123", "test")
    LogoutAction().execute(session)

    captured = capsys.readouterr()
    assert session.uid is None
    assert session.username is None
    assert "\nSuccessfully Logged Out.\n" in captured.out

#Test that the exit action flags the session as not running (which ends WellbeingApp.run's loop)
def test_exit_action(capsys):
    session = Session()
    ExitAction().execute(session)

    captured = capsys.readouterr()
    assert session.running is False
    assert "\nProgram terminated. Thank You!\n" in captured.out

# Checks that a successful login stores the user in the session
def test_login_action_success(capsys):
    accounts = MagicMock()
    accounts.login.return_value = AccountResult(True, "Login successful! Welcome, test!",
                                                uid="123", username="test")
    session = Session()
    LoginAction(accounts).execute(session)

    assert session.uid == "123"
    assert session.username == "test"
    assert "Login successful! Welcome, test!" in capsys.readouterr().out

# Checks that a failed login leaves the session logged out
def test_login_action_failure(capsys):
    accounts = MagicMock()
    accounts.login.return_value = AccountResult(False, "Invalid username or password.")
    session = Session()
    LoginAction(accounts).execute(session)

    assert not session.is_logged_in()
    assert "Invalid username or password." in capsys.readouterr().out

# --- Survey Tests ---

#Test that a user with an existing survey today is prevented from overwriting if they say 'no'
@patch.object(YesNoPrompt, 'ask', return_value=False)
@patch.object(AssessmentHistory, 'todays_records', return_value=[{'time': '10:00:00', 'record_id': 'abc'}])
@patch.object(Console, 'pause')
def test_survey_existing_record_kept(mock_pause, mock_todays_records, mock_yes_no, capsys):
    result = SurveyAction().collect_responses("test_uuid")

    captured = capsys.readouterr()
    assert result is None
    assert "You have already completed an assessment today" in captured.out
    assert "Your existing assessment for today has been kept." in captured.out
    mock_pause.assert_called_once()

# With no existing assessment today, the questionnaire runs straight away
@patch.object(Questionnaire, 'run', return_value={"user_id": None, "mood": "Calm"})
@patch.object(AssessmentHistory, 'todays_records', return_value=[])
def test_survey_runs_questionnaire_when_none_today(mock_todays_records, mock_run):
    result = SurveyAction().collect_responses("test_uuid")

    assert result == {"user_id": None, "mood": "Calm"}
    mock_run.assert_called_once()

# execute() hands the answers to process_responses(), which subclasses override
@patch.object(Questionnaire, 'run', return_value={"user_id": None, "mood": "Calm"})
@patch.object(AssessmentHistory, 'todays_records', return_value=[])
def test_survey_subclass_receives_responses(mock_todays_records, mock_run):
    received = []

    class RecordingSurvey(SurveyAction):
        def process_responses(self, session, responses):
            received.append((session.uid, responses))

    session = Session()
    session.log_in("123", "test")
    RecordingSurvey().execute(session)

    assert received == [("123", {"user_id": None, "mood": "Calm"})]