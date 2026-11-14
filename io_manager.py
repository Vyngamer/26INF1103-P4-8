'''
Main I/O Layer
'''

from flask_mail import mail, Message
from io_helpers.questionnaire import Questionnaire, SurveyAnswersError
from io_helpers.account_service import AccountService
from io_helpers.survey_result import SurveyResult

# I/O layer of web app
# app.py creates one IOManager and calls it from its routes.
# each action is given the logged-in user's id by the route (from Flask's session)
class IOManager:

    def __init__(self, data, process_responses=None):
        self.accounts = AccountService(data)
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
    EMAIL
    '''

    # send email (To counsellor, when user requires counselling follow-up)
    def send_email(recipient, uid, username, assessment: dict[str: str]):

        # Subjects & openings dependent on logic manager's given route

            ROUTES = {
                "Urgent support": ["Urgent Support Needed", "A Student requires urgent support."],
                "Counsellor follow-up": ["Counsellor Follow up Needed", "Our AI has flagged that this student requires counsellor follow-up."],
            }

            # Subject
            subject = ROUTES[assessment["route"]][0]
            opening = ROUTES[assessment["route"]][1]

            # Email body
            body = f'''
                Dear Counsellor,

                {opening}
                User ID = {uid}
                Username = {username}

                Here is a brief summary of the student scores:
                Sleep: {assessment["sleep_duration"]} Hr(s)
                Stress Level: {assessment["stress_level"]}
                Focus Level: {assessment["focus_level"]}
                Academic Workload: {assessment["academic_workload"]}
                Mood: {assessment["mood"]}
                Social Activity Level: {assessment["social_activity_level"]}
                Reflection: {assessment["reflection"]}

                This is the scores that the AI tabulated for them:
                Mental Wellness Risk Score: {assessment["mental_wellness_risk_score"]}
                Burnout Risk Score: {assessment["burnout_risk_score"]}

                This is the advice that our AI gave them:
                {assessment["personalized_recommendations"]}


                Please get in contact with this student ASAP.

                Best Regards,
                AI Counsellor
            '''
            
            try:
                msg = Message(subject=subject, recipients=[recipient], body=body)
                mail.send(msg)
                return True
            except Exception as e:
                print(f"Failed to send email: {e}")
                return False