import pytest
import sys
from unittest.mock import patch
import io_manager

# --- Session State Tests ---

#Test that a fresh session state initializes correctly
def test_new_state():
    state = io_manager.new_state()
    assert state == {"running": True, "uid": None, "username": None}

#Test that a user's ID and username are properly saved to the state
def test_set_logged_in():
    state = io_manager.new_state()
    io_manager.set_logged_in(state, "test_uuid_123", "test_user")
    
    assert state["uid"] == "test_uuid_123"
    assert state["username"] == "test_user"
    assert state["running"] is True

#Test the boolean check for user login status
def test_is_logged_in():
    state = io_manager.new_state()
    assert not io_manager.is_logged_in(state)
    
    io_manager.set_logged_in(state, "test_uuid_123", "test_user")
    assert io_manager.is_logged_in(state)

#Test that logging out correctly clears the user data but keeps the app running
def test_set_logged_out():
    state = {"running": True, "uid": "test_uuid_123", "username": "test_user"}
    io_manager.set_logged_out(state)
    
    assert state["uid"] is None
    assert state["username"] is None
    assert state["running"] is True

# --- Display Output Tests ---

#Test standard error output format
def test_print_error(capsys):
    io_manager.print_error("Invalid input")
    captured = capsys.readouterr()
    assert captured.out == "\nERROR: Invalid input\n"

#Test the standard notice output format
def test_print_notice(capsys):
    io_manager.print_notice("Action successful")
    captured = capsys.readouterr()
    assert captured.out == "\nNOTICE: Action successful\n"

#Test the standard welcome output format
def test_print_welcome(capsys):
    io_manager.print_welcome("Main Menu")
    captured = capsys.readouterr()
    assert captured.out == "\n---Main Menu---\n"

#Test the exit message output
def test_print_termination_msg(capsys):
    io_manager.print_termination_msg()
    captured = capsys.readouterr()
    assert captured.out == "\n\nProgram terminated. Thank You!\n"

# --- Menu & Handler Tests ---

#Test that the correct menu dictionary is returned based on login state
def test_current_menu():
    state = io_manager.new_state()
    
    #When logged out, should return MAIN_MENU
    assert io_manager.current_menu(state) == io_manager.MAIN_MENU
    
    #When logged in, should return USER_MENU
    io_manager.set_logged_in(state, "123", "test")
    assert io_manager.current_menu(state) == io_manager.USER_MENU

#Test that the logout handler updates the state and prints success message
def test_handle_logout(capsys):
    state = {"running": True, "uid": "123", "username": "test"}
    io_manager.handle_logout(state)
    
    captured = capsys.readouterr()
    assert state["uid"] is None
    assert state["username"] is None
    assert "\nSuccessfully Logged Out.\n" in captured.out

#Test that the exit handler flags the state as not running and calls sys.exit()
def test_handle_exit(capsys):
    state = io_manager.new_state()
    
    #Expect SystemExit exception when handle_exit is called
    with pytest.raises(SystemExit):
        io_manager.handle_exit(state)
        
    captured = capsys.readouterr()
    assert state["running"] is False
    assert "\nProgram terminated. Thank You!\n" in captured.out

#Test that a user with an existing survey today is prevented from overwriting if they say 'no'
@patch('io_manager.prompt_yes_no')
@patch('io_manager.get_todays_records')
@patch('io_manager.pause')
def test_handle_survey_existing_record_kept(mock_pause, mock_get_todays_records, mock_prompt_yes_no, capsys):
    # Mocking that the user already has a record today
    mock_get_todays_records.return_value = [{'time': '10:00:00', 'record_id': 'abc'}]
    # Mocking that the user chooses NOT to replace their existing assessment
    mock_prompt_yes_no.return_value = False
    
    result = io_manager.handle_survey("test_uuid")
    
    captured = capsys.readouterr()
    assert result is None
    assert "You have already completed an assessment today" in captured.out
    assert "Your existing assessment for today has been kept." in captured.out
    mock_pause.assert_called_once()