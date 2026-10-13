'''
Main I/O Layer
'''
import matplotlib.pyplot as plt
import sys
from questionnaire import full_survey, prompt_questionnaire
from prompts import prompt_choice, prompt_range, prompt_yes_no
from user import user_login, user_register, change_username, change_password
from data_manager import get_user_records, get_user_int_records, get_user_records, replace_user_record
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
    sys.exit()

'''
USER MENU HANDLERS
'''

#Handles survey and assessment
def handle_survey(uid):
    #If the user already has an assessment today, ask before replacing it
    todays = get_todays_records(uid, RECORDS)
    if todays:
        print(f"\nYou have already completed an assessment today (at {todays[0]['time']}).")

        if not prompt_yes_no("Only one assessment per day is allowed. "
                             "Replace today's assessment and start a new survey? (y/n): "):
            print("\nYour existing assessment for today has been kept.")
            pause()
            return

    #full_survey(LOGIC_FILE, AI_FILE, state["uid"])
    survey = prompt_questionnaire()

    #Replace the old record AFTER the new survey is finished,
    #so quitting/crashing halfway through keeps the existing assessment
    #if todays:
        #delete_records([record["record_id"] for record in todays], state["uid"], RECORDS)
    #    pass
    #pause()
    return survey

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
Graph
'''
def graph(user_id, records):
    pass

# graph
def show_graph(state):
    user_records = get_user_records(state["uid"], RECORDS)
    if len(user_records) < 2:
        print("You do not have enough records to do this comparison\nYou need to have at least 2 survey attempts")
        pause()
    else:
        required_data = get_user_int_records(user_records, state["uid"])
        index = 1
        x_axis = []
        while index <= len(required_data):
            x_axis.append(index)
            index += 1
        sleep_duration = []
        for sleep in required_data:
            sleep_duration.append(sleep["sleep_duration"])
        focus_level = []
        for focus in required_data:
            focus_level.append(focus["sleep_duration"])
        stress_level = []
        for stress in required_data:
            stress_level.append(stress["stress_level"])
        wellness_score = []
        for wellness in required_data:
            wellness_score.append(wellness["mental_wellness_risk_score"])
        burnout_risk_score = []
        for burnout in required_data:
            burnout_risk_score.append(burnout["burnout_risk_score"])

        # initialising the graph
        figure = plt.figure(figsize=(12, 8))
        figure.suptitle('Personal Wellness Tracking Dashboard', fontsize=16, fontweight='bold')
        grid_space = figure.add_gridspec(2, 6)


        # create graph 1 (sleep)
        ax1 = figure.add_subplot(grid_space[0, 0:2])
        ax1.set(xlabel='Attempts', ylabel='Hours (H)', title='Hours of Sleep')
        ax1.set_xticks(x_axis)
        ax1.set_ylim(0, 10)
        ax1.plot(x_axis, sleep_duration, marker='o', color='#1f77b4', linewidth=2)
        ax1.fill_between(x_axis, sleep_duration, color='#1f77b4', alpha=0.15)

        # create graph 2 (focus level)
        ax2 = figure.add_subplot(grid_space[0, 2:4])
        ax2.set(xlabel='Attempts', ylabel='Focus Level (1-10)', title='Your Focus Level')
        ax2.set_xticks(x_axis)
        ax2.set_ylim(0, 10)
        ax2.plot(x_axis, focus_level, marker='o', color='#ff7f0e', linewidth=2)
        ax2.fill_between(x_axis, focus_level, color='#ff7f0e', alpha=0.15)

        # create graph 3 (stress level)
        ax3 = figure.add_subplot(grid_space[0, 4:6])
        ax3.set(xlabel='Attempts', ylabel='Stress Level (1-10)', title='Your Stress Level')
        ax3.set_xticks(x_axis)
        ax3.set_ylim(0, 10)
        ax3.plot(x_axis, stress_level, marker='o', color='#d62728', linewidth=2)
        ax3.fill_between(x_axis, stress_level, color='#d62728', alpha=0.15)

        # create graph 4 (mental wellness score)
        ax4 = figure.add_subplot(grid_space[1, 0:3])
        ax4.set(xlabel='Attempts', ylabel='Mental wellness score (0-100)', title='Your Mental Wellness Scores')
        ax4.set_xticks(x_axis)
        ax4.set_ylim(0, 100)
        ax4.plot(x_axis, wellness_score, marker='o', color='#2ca02c', linewidth=2)
        ax4.fill_between(x_axis, wellness_score, color='#2ca02c', alpha=0.15)

        # create graph 5 (burnout risk score)
        ax5 = figure.add_subplot(grid_space[1, 3:6])
        ax5.set(xlabel='Attempts', ylabel='Burnout Risk Score (0-100)', title='Your Burnout Risk Scores')
        ax5.set_xticks(x_axis)
        ax5.set_ylim(0, 100)
        ax5.plot(x_axis, burnout_risk_score, marker='o', color='#9467bd', linewidth=2)
        ax5.fill_between(x_axis, burnout_risk_score, color='#9467bd', alpha=0.15)

        # displaying the graph
        plt.tight_layout()
        plt.show()
        pause()



'''
Assessment History
'''

#Assessment history: Show assessment history, then secondary menu for further details
def handle_history(state,db=RECORDS):
    while True:
        #Show the table again after every action, so it is always up to date
        view_assessment_history(state["uid"], db)
        if not get_user_records(state["uid"], db):
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
Graph functions
'''
def handle_graph(state, RECORDS):
    full_record = get_user_records(state["uid"], RECORDS)
    required_information = get_user_int_records(full_record, state["uid"])
    print(required_information)

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
    "View Graph": show_graph,
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