'''
Wellness assessment workflow
'''

import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from ai_manager_helper.data_classes.ai_output import AIOutput
from io_helpers.errors.AssessmentFailed import AssessmentFailed

_logger = logging.getLogger(__name__)


# Runs one assessment from validated survey answers to a saved record
# AI scores -> business rules -> merged record saved as today's -> counsellor email if needed
class AssessmentService:
    DATE_FORMAT = "%d-%m-%Y"
    TIMEZONE = ZoneInfo("Asia/Singapore")

    def __init__(self, io_manager, data_manager, logic_manager, mail, counsellor_email):
        self.__io_manager = io_manager
        self.__data_manager = data_manager
        self.__logic_manager = logic_manager
        self.__mail = mail
        self.__counsellor_email = counsellor_email

    # Check if user already has an assessment saved for today
    def done_today(self, uid):
        latest_record = self.__data_manager.get_latest_user_record(uid)
        today = datetime.now(self.TIMEZONE).strftime(self.DATE_FORMAT)
        return latest_record is not None and latest_record.get_date() == today

    # Checks the chatbot's answers with the IO Manager's questionnaire (returns a SurveyResult)
    def validate(self, uid, raw_answers):
        return self.__io_manager.survey(uid, raw_answers)

    # Assesses validated SurveyResponse answers and returns the saved AssessmentRecord
    # Raises AssessmentFailed if any step fails, so nothing half-done is shown or saved
    def assess(self, uid, username, responses, chat):
        try:
            user_input = responses.to_dict()
            ai_output = self.__ai_scores(chat, user_input)
            previous_attempts = self.__data_manager.get_previous_attempts(uid)
            logic_output = self.__logic_manager.assess(responses, AIOutput(**ai_output), previous_attempts).to_dict()

            # merge into one record and save it as today's (replacing any earlier one from same date)
            record = self.__data_manager.merge_record(user_input, ai_output, logic_output)
            if not self.__data_manager.replace_user_record(uid, record):
                raise AssessmentFailed("The assessment could not be saved.")
        except AssessmentFailed:
            raise
        except Exception as error:
            raise AssessmentFailed(f"The assessment could not be finished: {error}") from error

        # Counselling recommended (Urgent support or Counsellor follow-up route): email the counsellor.
        # The record is already saved, so a failed email is logged instead of failing the assessment.
        if logic_output["counselling_recommendation"]:
            self.__notify_counsellor(uid, username, record)
        return record
    
    def send_emergency_email(self, uid, username):
        if not self.__io_manager.send_email_crisis_detected(self.__counsellor_email, username, self.__mail):
            _logger.error("Counsellor email could not be sent for user %s", uid)

    @staticmethod
    def __ai_scores(chat, user_input):
        return chat.analyse(user_input)

    def __notify_counsellor(self, uid, username, record):
        if not self.__io_manager.send_email(self.__counsellor_email, username, record, self.__mail):
            _logger.error("Counsellor email could not be sent for user %s", uid)
    