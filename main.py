# import questionnaire
# import io_manager
# import data_manager
# import ai_manager
# import logic_manager
# import json

# user_id = 'user1'
# database_file = 'records.json'

# user_input = questionnaire.prompt_questionnaire()
# interaction = ai_manager.generate_survey_response(user_input)

# interaction_id = interaction.id
# ai_output = json.loads(interaction.output_text)

# print(ai_output)

# logic_output = logic_manager.assess(user_input, ai_output)

# record = {
#     "user_input": user_input,
#     "ai_output": ai_output,
#     "logic_output": logic_output
# }

# data_manager.save(record, database_file, user_id)

# import questionnaire
# import io_manager
# import data_manager
# import ai_manager
# import logic_manager
# import json

# #user_id = 'user1'
# database_file = 'records.json'


# # run the welcome menu
# print(io_manager.io_main())

# user_input = questionnaire.prompt_questionnaire()
# interaction = ai_manager.generate_survey_response(user_input)

# interaction_id = interaction.id
# ai_output = json.loads(interaction.output_text)

# print(ai_output)

# logic_output = logic_manager.assess(user_input, ai_output)

# record = {
#     "user_input": user_input,
#     "ai_output": ai_output,
#     "logic_output": logic_output
# }

# data_manager.save(record, database_file, user_id)

import json
import io_manager
import questionnaire
import ai_manager
import logic_manager
import data_manager
import history

DATABASE_FILE = 'records.json'

def run_real_survey(user_id):
    """Executes the full survey flow with real AI and logic integration."""
    print("\n--- Starting Wellness Survey ---")
    
    # Prompt questionnaire and assign the active user's ID
    user_input = questionnaire.prompt_questionnaire()
    user_input["user_id"] = user_id

    # Call the AI Manager
    print("\nAnalyzing your responses with AI. Please wait...")
    try:
        interaction = ai_manager.generate_survey_response(user_input, None)
        ai_output = json.loads(interaction.output_text)
    except Exception as e:
        print(f"\nError communicating with the AI or parsing response: {e}")
        return

    # Retrieve previous attempts required for logic assessment
    previous_attempts = data_manager.get_user_records(user_id, DATABASE_FILE)

    # Process business rules
    logic_output = logic_manager.assess(user_input, ai_output, previous_attempts)

    savable_data = logic_manager.get_saveable_output(logic_output)
    display_messages = logic_manager.get_display_messages(logic_output)
    # Merge and save the record to the database
    record = data_manager.merge_record(user_input, ai_output, savable_data)
    data_manager.save(record, DATABASE_FILE)

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
            run_real_survey(state["uid"])
        elif func == io_manager.handle_history:
            history.view_assessment_history(state["uid"], DATABASE_FILE)
            io_manager.pause()
        else:
            # Executes Login, Register, Exit, Change Username/Password, or Logout
            func(state)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nProgram terminated. Thank You!")

def survey():
    user_id = 'user1'
    database_file = 'records.json'

    user_input = questionnaire.prompt_questionnaire()
    interaction = ai_manager.generate_survey_response(user_input)

    interaction_id = interaction.id
    ai_output = json.loads(interaction.output_text)

    print(ai_output)

    logic_output = logic_manager.assess(user_input, ai_output)

    record = {
        "user_input": user_input,
        "ai_output": ai_output,
        "logic_output": logic_output
    }

    data_manager.save(record, database_file)


if __name__ == "__main__":
    survey()