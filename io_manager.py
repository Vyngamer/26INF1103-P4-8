'''
Main I/O Layer
'''

from questionnaire import full_survey
from prompts import prompt_choice, prompt_range, prompt_yes_no
from user import user_login, user_register, change_username, change_password
from data_manager import get_user_records
from history import view_assessment_history, view_assessment_details, view_wellbeing_summary, get_todays_records, delete_records
from title import print_title

#I/O Files
LOGIC_FILE = "logic_sample.json"
AI_FILE = "ai_sample.json"
RECORDS = "records.json"

'''
SET TO FALSE FOR REAL USE

True: For standalone console to call menu functions directly
False: Return (option no., func) and let main program call
'''
TEST_MODE = False

'''
Session State
'''
#Fresh session state
def new_state():
    return {"running": True, "uid": None, "username": None}

#Check if a user is logged in
def is_logged_in(state):
    return state["uid"] is not None

#Change state to logged in
def set_logged_in(state, uid, username):
    state["uid"] = uid
    state["username"] = username

#Change state to logged out
def set_logged_out(state):
    state["uid"] = None
    state["username"] = None

#Allow user to enter to return to menu
def pause():
    input("\nPress Enter to return to the menu...")

'''
MAIN MENU HANDLERS
'''

#User registration
def handle_register(state):
    result = user_register()
    print(result["message"])

#User login
def handle_login(state):
    result = user_login()
    print(f"\n{result['message']}")
    if result["ok"]:
        set_logged_in(state, result["uid"], result["username"])

#Exit program
def handle_exit(state):
    print("\nProgram terminated. Thank You!")
    state["running"] = False

'''
USER MENU HANDLERS
'''

#Handles survey and assessment
def handle_survey(state):
    #If the user already has an assessment today, ask before replacing it
    todays = get_todays_records(state["uid"], RECORDS)
    if todays:
        print(f"\nYou have already completed an assessment today (at {todays[0]['time']}).")

        if not prompt_yes_no("Only one assessment per day is allowed. "
                             "Replace today's assessment and start a new survey? (y/n): "):
            print("\nYour existing assessment for today has been kept.")
            pause()
            return

    full_survey(LOGIC_FILE, AI_FILE, state["uid"])

    #Replace the old record AFTER the new survey is finished,
    #so quitting/crashing halfway through keeps the existing assessment
    if todays:
        delete_records([record["record_id"] for record in todays], state["uid"], RECORDS)
    pause()

#Change username
def handle_change_username(state):
    result = change_username(state["uid"])
    print(result["message"])
    if result["ok"]:
        state["username"] = result["username"]
    pause()

#Change password
def handle_change_password(state):
    result = change_password(state["uid"])
    print(result["message"])
    pause()

#User logout
def handle_logout(state):
    set_logged_out(state)
    print("\nSuccessfully Logged Out.")

'''
Assessment History
'''

#Assessment history: Show assessment history, then secondary menu for further details
def handle_history(state):
    while True:
        #Show the table again after every action, so it is always up to date
        view_assessment_history(state["uid"], RECORDS)
        if not get_user_records(state["uid"], RECORDS):
            pause()
            return
        option, func = choose_option(HISTORY_MENU)
        if func is None:    #Go Back
            return
        func(state)    

#Ask which assessment, by its No. in the history table. Returns that number (0 = cancel)
def prompt_assessment_number(state, action):
    total = len(get_user_records(state["uid"], RECORDS))
    return prompt_range(f"Enter the No. of the assessment to {action} (1-{total}, or 0 to cancel): ", 0, total)

#View one assessment from the history table in detail
def handle_history_details(state):
    number = prompt_assessment_number(state, "view")
    if number == 0:
        return
    view_assessment_details(get_user_records(state["uid"], RECORDS)[number - 1])
    pause()

#View the well-being summary
def handle_history_summary(state):
    view_wellbeing_summary(state["uid"], RECORDS)
    pause()

'''
MENUS
'''

MAIN_MENU = {
    "Register New User": handle_register,
    "Login": handle_login,
    "Exit": handle_exit
}

USER_MENU = {
    "Start Survey": handle_survey,
    "View History": handle_history,
    "Change Username": handle_change_username,
    "Change Password": handle_change_password,
    "Logout": handle_logout
}

HISTORY_MENU = {
    "View Assessment Details": handle_history_details,
    "View Summary": handle_history_summary,
    "Back": None
}

#Identify which menu to show depending if user is logged in
def current_menu(state):
    if is_logged_in(state):
        return USER_MENU
    else:
        return MAIN_MENU

#Show a menu, then return option no. & associated function
def choose_option(menu):
    labels = list(menu)
    label = prompt_choice(labels,
                          "\n---------MENU---------",
                          f"Enter option (1-{len(menu)}): ",
                          "----------------------\n")
    return labels.index(label) + 1, menu[label]

#Main menu
def run_menu(menu,state):
    option, func = choose_option(menu)
    #Call function if testing, else return option no. and function object
    if TEST_MODE:
        func(state)
    else:
        return option, func

'''
MAIN PROGRAM
'''

#Main Program
def io_main(state=None):
    if state is None:
        state = new_state()

    #If not testing, return option no. & function for main prog
    if not TEST_MODE:
        return run_menu(current_menu(state), state)
    
    #Title
    title = "STUDENT WELLBEING SUPPORT SYSTEM"
    print_title(title)

    #If testing, loop & call directly in terminal
    while state["running"]:
        run_menu(current_menu(state), state)
    
#test
if __name__ == "__main__":
    try:
        if TEST_MODE:
            print("TEST MODE: TRUE")
            io_main()
        else:
            print("TEST MODE: FALSE")
            state = new_state()
            title = "STUDENT WELLBEING SUPPORT SYSTEM"
            print_title(title)
            while state["running"]:
                i, func = io_main(state)
                print(f"TEST: io_main returned: ({i}, {func.__name__})")
                func(state)
    except (KeyboardInterrupt, EOFError):
        print("\n\nProgram terminated. Thank You!")