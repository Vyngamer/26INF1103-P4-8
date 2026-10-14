import json
import io_manager
import questionnaire
import ai_manager
from ai_manager import client
import logic_manager
import data_manager
import history

DATABASE_FILE = 'records.json'

def run_real_survey(user_id):
    """Executes the full survey flow with real AI and logic integration."""
    io_manager.print_welcome("Starting Wellness Survey")
    
    # Prompt questionnaire and assign the active user's ID
    #user_input = questionnaire.prompt_questionnaire()
    user_input = io_manager.handle_survey(user_id)
    if user_input is None:
        return
    user_input["user_id"] = user_id

    # Call the AI Manager
    io_manager.print_notice("Analyzing your responses with AI. Please wait...")
    try:
        interaction = ai_manager.generate_survey_response(user_input, None)
    except Exception as e:
        io_manager.print_error(f"Error communicating with the AI or parsing response: {e}")
        return

    ai_output = ai_manager.parse_response(interaction)

    # Retrieve previous attempts required for logic assessment
    previous_attempts = data_manager.get_previous_attempts(user_id, DATABASE_FILE)

    # Process business rules
    logic_output = logic_manager.assess(user_input, ai_output, previous_attempts)

    # Merge and save the record to the database
    record = data_manager.merge_record(user_input, ai_output, logic_output)
    data_manager.replace_user_record(user_id, record, DATABASE_FILE)

    # Display the final assessment to the user
    history.view_latest_assessment(user_id, DATABASE_FILE)
    
    io_manager.pause()

def main():
    # Initialize the session state to track the active user
    state = io_manager.new_state()
    io_manager.print_title("Welcome To Our Wellness Checker")

    # Main application loop that dynamically switches menus based on login state
    while state["running"]:
        # current_menu returns MAIN_MENU if logged out, or USER_MENU if logged in
        menu = io_manager.current_menu(state)
        option, func = io_manager.choose_option(menu)

        # Intercept dummy functions to use the real connected modules
        if func == io_manager.handle_survey:
            if not client:
                io_manager.print_error("AI functionality down. Please try again later!")
            else:
                run_real_survey(state["uid"])
        elif func == io_manager.handle_history:
            io_manager.handle_history(state, DATABASE_FILE)
        else:
            # Executes Login, Register, Exit, Change Username/Password, or Logout
            func(state)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        io_manager.print_termination_msg()