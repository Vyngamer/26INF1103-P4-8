'''
Wellness check pages: chatbot survey, confirmation & submission
'''

from flask import render_template, request, redirect, url_for, session

from app_helpers.routes.RouteGroup import RouteGroup
from io_helpers.errors.AssessmentFailed import AssessmentFailed
from ai_manager_helper.crisis_safety_filter import CrisisDetectedError


# Connects the chatbot page to the user's ChatSession and the AssessmentService.
class WellnessRoutes(RouteGroup):
    SURVEY_DENIED = "The survey results are not accurate."
    ASSESSMENT_FAILED = "Sorry, I couldn't finish your assessment just now. Please press Yes to try again."

    def __init__(self, user_session, chat_registry, assessment_service):
        super().__init__(user_session)
        self.__chat_registry = chat_registry
        self.__assessments = assessment_service

    def _routes(self):
        # One view for both wellness-check URLs (Flask needs the same function for one endpoint)
        wellness_check = self._protected(self.__wellness_check)
        return [
            ("/wellness-check", "wellness_check", wellness_check, ["GET"]),
            ("/wellness-check/<continue_chat>/<crisis_detected>", "wellness_check", wellness_check, ["GET"]),
            ("/reset-conversation", "reset_conversation", self._protected(self.__reset_conversation), ["GET"]),
            ("/get", "chat", self._protected(self.__chat), ["POST"]),
            ("/get-bot-response", "wait_for_bot_response", self._protected(self.__wait_for_bot_response), ["GET"]),
            ("/confirm-survey", "confirm_survey", self._protected(self.__confirm_survey), ["GET"]),
            ("/submit_survey", "submit_survey", self._protected(self.__submit_survey), ["GET"]),
            ("/deny-survey", "deny_survey", self._protected(self.__deny_survey), ["GET"]),
            ("/crisis-detected", "crisis_detected", self._protected(self.__crisis_detected), ["GET"]),
        ]

    def __wellness_check(self, uid, username, continue_chat=False, crisis_detected=False):
        chat = self.__chat_registry.get(uid)
        chat.start()
        return render_template("wellness-check.html", conversation=chat.conversation, survey_results=None,
                               already_done_today=not continue_chat and self.__assessments.done_today(uid), crisis_detected=crisis_detected)

    def __reset_conversation(self, uid, username):
        self.__chat_registry.discard(uid)
        return redirect(url_for("wellness_check"))

    # User message
    # returns the chatbot's reply as JSON for the page's script
    def __chat(self, uid, username):
        try:
            return {'data': self.__chat_registry.get(uid).send(request.form["msg"]), 'crisis_detected': False}
        except CrisisDetectedError:
            session["crisis_email_pending"] = True
            return {'data': {}, 'crisis_detected': True}
            

    # Waits for a bot reply that was started in the background
    def __wait_for_bot_response(self, uid, username):
        return self.__chat_registry.get(uid).wait_for_reply()

    # Shows the collected answers with Yes / No buttons
    def __confirm_survey(self, uid, username):
        chat = self.__chat_registry.get(uid)
        survey_results = chat.survey_answers(by_alias=True)
        if survey_results is None:
            return redirect(url_for("wellness_check", continue_chat=True))
        return render_template("wellness-check.html", conversation=chat.conversation, survey_results=survey_results)

    def __submit_survey(self, uid, username):
        chat = self.__chat_registry.get(uid)
        raw_answers = chat.survey_answers()
        if raw_answers is None:
            return redirect(url_for("wellness_check", continue_chat=True))

        survey_result = self.__assessments.validate(uid, raw_answers)
        if not survey_result.result:    # If an answer is invalid, chatbot asks the user to fix it
            chat.deny_survey(f"Some answers need to be fixed: {survey_result.message}")
            return redirect(url_for("wellness_check"))

        try:
            record = self.__assessments.assess(uid, username, survey_result.response, chat)
        except AssessmentFailed as e:
            chat.notify(self.ASSESSMENT_FAILED)
            return redirect(url_for("confirm_survey"))    # shows the answers again with Yes / No

        # The assessment is finished, so the next wellness check starts a new chat.
        # Redirect, so refreshing the results page doesn't run the assessment (and the email) again
        self.__chat_registry.discard(uid)
        return redirect(url_for("result", attempt_id=record.get_record_id()))

    def __deny_survey(self, uid, username):
        self.__chat_registry.get(uid).deny_survey(self.SURVEY_DENIED)
        return redirect(url_for("wellness_check", continue_chat=True))
    
    def __crisis_detected(self, uid, username):
        if not session.pop("crisis_email_pending", False):
            return redirect(url_for("dashboard"))
        
        chat = self.__chat_registry.get(uid)
        self.__chat_registry.discard(uid)
        self.__assessments.send_emergency_email(uid, username)

        return render_template("dashboard.html", conversation=chat.conversation, crisis_detected=True)