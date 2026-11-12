'''
Main I/O Layer
'''

from io_helpers.questionnaire import Questionnaire, SurveyAnswersError
from io_helpers.account_service import AccountService
from io_helpers.trends import trend_points
from io_helpers.survey_response import SurveyResult

# I/O layer of web app
# app.py creates one IOManager and calls it from its routes.
# each action is given the logged-in user's id by the route (from Flask's session)
class IOManager:

    def __init__(self, data, process_responses=None, accounts=None):
        self.data = data
        self.accounts = accounts or AccountService(data)
        self.process_responses = process_responses

    '''
    ACCOUNT ACTIONS
    '''

    # User registration
    def register(self, username, password, confirm):
        return self.accounts.register(username, password, confirm)

    # User login
    def login(self, username, password):
        return self.accounts.login(username, password)

    # Change username
    def change_username(self, uid, new_username):
        return self.accounts.change_username(uid, new_username)

    # Change password
    def change_password(self, uid, current_password, new_password, confirm):
        return self.accounts.change_password(uid, current_password, new_password, confirm)

    # Get username of the logged-in user, or None if their account no longer exists
    def get_username(self, uid):
        return self.accounts.get_username(uid)

    '''
    SURVEY
    '''

    # Handles survey and assessment.
    # Valid answers are handed to process_responses (if given) for further handling.
    # Returns a SurveyResult; when ok is False, errors shows which answers are invalid
    def survey(self, uid, answers):
        try:
            responses = Questionnaire().from_answers(uid, answers)
        except SurveyAnswersError as error:
            return SurveyResult(False, str(error), errors=error.errors)
        if self.process_responses is not None:
            self.process_responses(uid, responses)
        return SurveyResult(True, "Survey answers accepted.", response=responses)

    '''
    ASSESSMENT TRENDS
    '''

    # Assessment trends
    # Returns the progress page's graph data, oldest -> newest, or None if there are fewer than 2 assessments
    def trends(self, uid):
        return trend_points(self.data, uid)