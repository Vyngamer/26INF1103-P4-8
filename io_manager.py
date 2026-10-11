'''
Main I/O Layer
'''

from questionnaire import full_survey
from prompts import prompt_choice
from user import user_login, user_register, change_username, change_password

#I/O Files
SURVEY_FILE = "results.json"
LOGIC_FILE = "logic_sample.json"
AI_FILE = "ai_sample.json"

'''
For Testing
Set True to call menu functions directly
Set False to return function objects for main program to call
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
    full_survey(SURVEY_FILE, LOGIC_FILE, AI_FILE)
    pause()

#User history
def handle_history(state):
    print("This functionality has not been implemented yet.")
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

#Title
def print_title():
    print("============================")
    print("Welcome to Mental Health Tool")
    print("============================")

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
    print_title()

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
            print_title()
            while state["running"]:
                i, func = io_main(state)
                print(f"TEST: io_main returned: ({i}, {func.__name__})")
                func(state)
    except (KeyboardInterrupt, EOFError):
        print("\n\nProgram terminated. Thank You!")