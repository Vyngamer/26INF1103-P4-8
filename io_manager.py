'''
Main I/O Layer
'''

from io_helpers.questionnaire import Questionnaire
from io_helpers.prompts import ChoicePrompt, RangePrompt, YesNoPrompt
from io_helpers.account_service import AccountService
from io_helpers.history import todays_records, AssessmentHistoryTable, AssessmentDetailView
from data_manager import DataManager
from pymongo.errors import PyMongoError
from io_helpers.trends import show_trends
from io_helpers.console import Console
from io_helpers.session import Session

# Whole console application
class IOManager:
    MENU_HEADING = "\n---------MENU---------"
    MENU_FOOTER = "----------------------\n"

    def __init__(self, process_responses=None, data=None,
                 title="STUDENT WELLBEING SUPPORT SYSTEM", accounts=None):
        self.title = title
        self._data = data
        self.session = Session()
        self._accounts = accounts
        self.process_responses = process_responses

        # Menu Lists
        self.main_menu = [
            ("Register New User", self.register),
            ("Login", self.login),
            ("Exit", self.exit),
        ]

        self.user_menu = [
            ("Start Survey", self.survey),
            ("View History", self.history),
            ("Change Username", self.change_username),
            ("Change Password", self.change_password),
            ("View Assessment Trends", self.trends),
            ("Logout", self.logout),
        ]

    # Shared DataManager object. If none was passed in, one is created the first time it is needed
    # not in __init__, because creating one connects to MongoDB Atlas
    @property
    def data(self):
        if self._data is None:
            self._data = DataManager()
        return self._data

    # Shared AccountService for every account action, using the same DataManager
    @property
    def accounts(self):
        if self._accounts is None:
            self._accounts = AccountService(self.data)
        return self._accounts

    # Show a menu, then return the method for the chosen option
    # (None for an option with no method, e.g. "Back")
    def choose(self, menu):
        labels = [label for label, _ in menu]
        chosen = ChoicePrompt(labels, self.MENU_HEADING,
                              f"Enter option (1-{len(labels)}): ",
                              self.MENU_FOOTER).ask()
        return dict(menu)[chosen]

    #Identify which menu to show depending if user is logged in
    def current_menu(self):
        return self.user_menu if self.session.is_logged_in() else self.main_menu

    #Show the title, then keep showing the right menu and running the chosen action
    def run(self):
        Console.title(self.title)
        while self.session.running:
            self.choose(self.current_menu())()

    '''
    MAIN MENU ACTIONS
    '''

    # User registration
    def register(self):
        result = self.accounts.register()
        print(result.message)

    # User login
    def login(self):
        result = self.accounts.login()
        print(f"\n{result.message}")
        if result.ok:
            self.session.log_in(result.uid, result.username)

    # Exit program
    # Stops run()'s loop so the program ends normally
    def exit(self):
        Console.termination_msg()
        self.session.running = False

    '''
    USER MENU ACTIONS
    '''

    # Handles survey and assessment.
    # Collect the answers, then hand them to process_responses (if given) for further handling.
    def survey(self):
        responses = self.collect_responses(self.session.uid)
        if responses is not None and self.process_responses is not None:
            self.process_responses(self.session, responses)

    #Run the questionnaire. Returns the answers, or None if the user kept today's assessment
    def collect_responses(self, uid):
        #If the user already has an assessment today, ask before replacing it
        todays = todays_records(self.data, uid)
        if todays:
            print(f"\nYou have already completed an assessment today (at {todays[0].get_time()}).")

            # Prompt user to confirm if they want to replace today's assessment
            try:
                replace = YesNoPrompt("Only one assessment per day is allowed. "
                                      "Replace today's assessment and start a new survey? (y/n): ").ask()
            # Ctrl+C returns to menu
            except (KeyboardInterrupt, EOFError):
                replace = False
            if not replace:
                print("\nYour existing assessment for today has been kept.")
                Console.pause()
                return None

        return Questionnaire().run(uid)

    # Change username
    def change_username(self):
        result = self.accounts.change_username(self.session.uid)
        print(result.message)
        if result.ok:
            self.session.username = result.username
        Console.pause()

    # Change password
    def change_password(self):
        result = self.accounts.change_password(self.session.uid)
        print(result.message)
        Console.pause()

    # User logout
    def logout(self):
        self.session.log_out()
        print("\nSuccessfully Logged Out.")

    # Show assessment trends graph
    def trends(self):
        show_trends(self.data, self.session.uid)

    '''
    ASSESSMENT HISTORY
    '''

    # Show assessment history, then secondary menu for further details
    def history(self):
        submenu = [("View Assessment Details", self.history_details), ("Back", None)]
        while True:
            #Show the table again after every action, so it is always up to date
            records = self.data.get_user_records(self.session.uid)
            if not records:
                print("\nNo assessment history found.")
                return
            AssessmentHistoryTable(records).show()
            action = self.choose(submenu)
            if action is None:    #Go Back
                return
            action()

    # View one assessment from the history table in detail.
    def history_details(self):
        records = self.data.get_user_records(self.session.uid)
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
RUN I/O MANAGER DIRECTLY
'''

def main():
    try:
        try:
            data = DataManager()
        except (ConnectionError, ValueError, PyMongoError) as error:
            Console.error(f"Could not open the database: {error}")
            return
        try:
            IOManager(data=data).run()
        finally:
            data.close()    # always close the MongoDB connection
    except (KeyboardInterrupt, EOFError):
        Console.termination_msg()


if __name__ == "__main__":
    main()