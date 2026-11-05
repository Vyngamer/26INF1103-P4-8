'''
Main I/O Layer
'''
import matplotlib.pyplot as plt
from matplotlib.backends import backend_registry, BackendFilter
from abc import ABC, abstractmethod 
from io_helpers.questionnaire import Questionnaire
from io_helpers.prompts import ChoicePrompt, RangePrompt, YesNoPrompt
from io_helpers.user import AccountService
from data_manager import get_user_records, get_user_int_records
from io_helpers.history import AssessmentHistory, AssessmentHistoryTable, AssessmentDetailView
from io_helpers.console import Console

#I/O Files
RECORDS = "records.json"

# Note: print_error & print_notice have been removed from io_manager.
# ai_manager.py, ai_manager_helper.py and ai_manager_refactor.py must change
# from io_manager import print_error, print_notice
# TO
# from io_helpers.console import Console
# and call Console.error(...) / Console.notice(...) instead.

'''
Session State
'''

# Session Class
class Session:
    def __init__(self):
        self.running = True
        self.uid = None
        self.username = None

    #Check if a user is logged in
    def is_logged_in(self):
        return self.uid is not None

    #Change state to logged in
    def log_in(self, uid, username):
        self.uid = uid
        self.username = username

    #Change state to logged out
    def log_out(self):
        self.uid = None
        self.username = None


'''
MENU ACTIONS
'''

# Abstract base class for every menu option.
# __str__ returns the label so actions can be listed by ChoicePrompt directly.
class MenuAction(ABC):
    label = ""
    closes_menu = False    #True for "Back" - tells a sub-menu loop to stop

    def __str__(self):
        return self.label

    @abstractmethod
    def execute(self, session):
        pass


# Shared base for actions that use the account service (register, login, ...)
class AccountAction(MenuAction):
    def __init__(self, accounts=None):
        self.accounts = accounts or AccountService()


'''
MAIN MENU ACTIONS
'''

# Originally handle_register() - User registration
class RegisterAction(AccountAction):
    label = "Register New User"

    def execute(self, session):
        result = self.accounts.register()
        print(result.message)


# Originally handle_login() - User login
class LoginAction(AccountAction):
    label = "Login"

    def execute(self, session):
        result = self.accounts.login()
        print(f"\n{result.message}")
        if result.ok:
            session.log_in(result.uid, result.username)


# Originally handle_exit() - Exit program
class ExitAction(MenuAction):
    label = "Exit"

    #Stops IOManager.run()'s loop so the program ends normally (no sys.exit needed)
    def execute(self, session):
        Console.termination_msg()
        session.running = False

'''
USER MENU ACTIONS
'''

# Originally handle_survey() - Handles survey and assessment.
class SurveyAction(MenuAction):
    label = "Start Survey"

    def __init__(self, db=RECORDS):
        self.db = db

    #Collect the answers, then hand them to process_responses() for further handling.
    def execute(self, session):
        responses = self.collect_responses(session.uid)
        if responses is not None:
            self.process_responses(session, responses)

    #Run the questionnaire. Returns the answers, or None if the user kept today's assessment
    def collect_responses(self, uid):
        #If the user already has an assessment today, ask before replacing it
        todays = AssessmentHistory(uid, self.db).todays_records()
        if todays:
            print(f"\nYou have already completed an assessment today (at {todays[0]['time']}).")

            # Prompt user to confirm if they want to replace today's assessment
            if not YesNoPrompt("Only one assessment per day is allowed. "
                               "Replace today's assessment and start a new survey? (y/n): ").ask():
                print("\nYour existing assessment for today has been kept.")
                Console.pause()
                return None

        return Questionnaire().run()

    #Hook for subclasses: what to do with the answers
    def process_responses(self, session, responses):
        pass


# Originally handle_change_username() - Change username
class ChangeUsernameAction(AccountAction):
    label = "Change Username"

    def execute(self, session):
        result = self.accounts.change_username(session.uid)
        print(result.message)
        if result.ok:
            session.username = result.username
        Console.pause()


# Originally handle_change_password() - Change password
class ChangePasswordAction(AccountAction):
    label = "Change Password"

    def execute(self, session):
        result = self.accounts.change_password(session.uid)
        print(result.message)
        Console.pause()


# Originally handle_logout() - User logout
class LogoutAction(MenuAction):
    label = "Logout"

    def execute(self, session):
        session.log_out()
        print("\nSuccessfully Logged Out.")


# Generic "Back" option for sub-menus
class BackAction(MenuAction):
    label = "Back"
    closes_menu = True

    def execute(self, session):
        pass

'''
Graph
'''

class TrendsAction(MenuAction):
    label = "View Assessment Trends"
    OUTPUT_FILE = "graph.png"

    # (data key, grid row, grid columns, y-label, title, y-max, colour)
    CHARTS = [
        ("sleep_duration",             0, slice(0, 2), 'Hours (H)',                     'Hours of Sleep',               24,  '#1f77b4'),
        ("focus_level",                0, slice(2, 4), 'Focus Level (1-10)',            'Your Focus Level',             10,  '#ff7f0e'),
        ("stress_level",               0, slice(4, 6), 'Stress Level (1-10)',           'Your Stress Level',            10,  '#d62728'),
        ("social_activity_level",      0, slice(6, 8), 'Social Activity Level (1-10)',  'Your Social Activity Level',   10,  '#b1bd22'),
        ("mental_wellness_risk_score", 1, slice(0, 4), 'Mental wellness score (0-100)', 'Your Mental Wellness Scores',  100, '#2ca02c'),
        ("burnout_risk_score",         1, slice(4, 8), 'Burnout Risk Score (0-100)',    'Your Burnout Risk Scores',     100, '#9467bd'),
    ]

    def __init__(self, db=RECORDS):
        self.db = db

    #Check if matplotlib can open a window (False when there is no display, e.g. headless Docker)
    @staticmethod
    def can_show_window():
        interactive = backend_registry.list_builtin(BackendFilter.INTERACTIVE)
        return plt.get_backend().lower() in [b.lower() for b in interactive]

    def execute(self, session):
        user_records = get_user_records(session.uid, self.db)
        if len(user_records) < 2:
            print("You do not have enough records to do this comparison\nYou need to have at least 2 survey attempts")
            Console.pause()
            return

        #As records are stored newest first; reverse so the graph runs oldest -> newest
        required_data = get_user_int_records(user_records, session.uid)[::-1]
        x_axis = list(range(1, len(required_data) + 1))

        # initialising the graph
        figure = plt.figure(figsize=(12, 8))
        figure.suptitle('Personal Wellness Tracking Dashboard', fontsize=16, fontweight='bold')
        grid_space = figure.add_gridspec(2, 8)

        # create each graph
        for key, row, columns, ylabel, title, ymax, colour in self.CHARTS:
            values = [entry[key] for entry in required_data]
            axis = figure.add_subplot(grid_space[row, columns])
            axis.set(xlabel='Attempts', ylabel=ylabel, title=title)
            axis.set_xticks(x_axis)
            axis.set_ylim(0, ymax)
            axis.plot(x_axis, values, marker='o', color=colour, linewidth=2)
            axis.fill_between(x_axis, values, color=colour, alpha=0.15)

        # displaying the graph
        plt.tight_layout()
        plt.savefig(self.OUTPUT_FILE)

        if self.can_show_window():
            Console.notice(f'Graph saved as {self.OUTPUT_FILE}. Close the graph window to continue...')
            plt.show()  #Blocks until the graph window is closed
            plt.close(figure)
        else:
            #No display (e.g. Docker without X11), so the graph can only be saved
            plt.close(figure)
            Console.notice(f'No display found, graph saved as {self.OUTPUT_FILE}')
            Console.pause()

'''
Assessment History
'''

# Originally handle_history() - Show assessment history, then secondary menu for further details
class HistoryAction(MenuAction):
    label = "View History"

    def __init__(self, db=RECORDS):
        self.db = db
        self.menu = Menu([HistoryDetailsAction(db), BackAction()])

    def execute(self, session):
        history = AssessmentHistory(session.uid, self.db)
        while True:
            #Show the table again after every action, so it is always up to date
            records = history.records()
            if not records:
                print("\nNo assessment history found.")
                return
            AssessmentHistoryTable(records).show()
            action = self.menu.choose()
            if action.closes_menu:    #Go Back
                return
            action.execute(session)


# Originally handle_history_details() + prompt_assessment_number().
# View one assessment from the history table in detail.
class HistoryDetailsAction(MenuAction):
    label = "View Assessment Details"

    def __init__(self, db=RECORDS):
        self.db = db

    def execute(self, session):
        records = AssessmentHistory(session.uid, self.db).records()
        number = self.prompt_assessment_number(len(records))
        if number == 0:
            return
        AssessmentDetailView(records[number - 1]).show()
        Console.pause()

    #Ask which assessment, by its No. in the history table. Returns that number (0 = cancel)
    @staticmethod
    def prompt_assessment_number(total):
        return RangePrompt(f"Enter the No. of the assessment to view (1-{total}, or 0 to cancel): ",
                           0, total).ask()

'''
MENUS
'''

# List of MenuAction objects
class Menu:
    def __init__(self, actions):
        self.actions = list(actions)

    # Show the menu, prompt user to choose an option
    # Return the chosen action
    def choose(self):
        return ChoicePrompt(self.actions,
                            "\n---------MENU---------",
                            f"Enter option (1-{len(self.actions)}): ",
                            "----------------------\n").ask()


# Whole console application
# main.py creates one object and passes in its own SurveyAction subclass
class IOManager:
    def __init__(self, survey_action=None, db=RECORDS, title="STUDENT WELLBEING SUPPORT SYSTEM"):
        self.title = title
        self.session = Session()
        accounts = AccountService()    # one shared service for every account action
        if survey_action is None:
            survey_action = SurveyAction(db)
        self.main_menu = Menu([RegisterAction(accounts), LoginAction(accounts), ExitAction()])
        self.user_menu = Menu([
            survey_action,
            HistoryAction(db),
            ChangeUsernameAction(accounts),
            ChangePasswordAction(accounts),
            TrendsAction(db),
            LogoutAction()
        ])

    #Identify which menu to show depending if user is logged in
    def current_menu(self):
        return self.user_menu if self.session.is_logged_in() else self.main_menu

    #Show the title, then keep showing the right menu and running the chosen action
    def run(self):
        Console.title(self.title)
        while self.session.running:
            self.current_menu().choose().execute(self.session)

'''
RUN I/O MANAGER DIRECTLY
'''

if __name__ == "__main__":
    try:
        IOManager().run()
    except (KeyboardInterrupt, EOFError):
        Console.termination_msg()