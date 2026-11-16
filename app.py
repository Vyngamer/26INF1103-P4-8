import re
import os
import threading
import sys
import markdown
import logic_manager
import json
from datetime import date

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_mail import Mail
from dotenv import load_dotenv
from markupsafe import escape
from ai_manager import AIManager
from data_manager import DataManager
from data_manager_helper.hasher import PasswordHasher
from io_helpers.errors.assessment_error import AssessmentFailed
from pydantic import ValidationError
from io_manager import IOManager
from ai_manager_helper.data_classes.conversation import Conversation
from ai_manager_helper.data_classes.survey_entity_schema import SurveyEntitySchema
from ai_manager_helper.api_client_classes.gemini_client import GeminiClient
from ai_manager_helper.data_classes.ai_output import AIOutput
from logic_manager_helper.LogicManager import LogicManager

ai_manager = AIManager()
ai_manager.connect_client()
data_manager = DataManager()
logic_manager = LogicManager()
io_manager = IOManager(data_manager)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

conversation = Conversation()

# email config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

# mail recepient
mail_recipient = app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

# Returns the logged-in user's id and username, or (None, None) if nobody is logged in
# or their account no longer exists (e.g. it was deleted in another tab)
def current_user():
    uid = session.get('user_id')
    user = data_manager.get_user_by_id(uid) if uid else None
    username = user.get_username() if user else None
    if username is None:
        session.pop('user_id', None)
        return None, None
    return uid, username


# route for index, this will be the default page when the app runs
@app.route("/")
def main():
    return render_template("index.html")

# route for register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        result = io_manager.register(request.form.get("username"), request.form.get("password"),
                                     request.form.get("confirm"))
        if not result.ok:
            return render_template("register.html", error=result.message)
        flash(result.message)
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        result = io_manager.login(request.form.get("username"), request.form.get("password"))
        if not result.ok:
            return render_template("login.html", error=result.message)
        session['user_id'] = result.uid
        return redirect(url_for("dashboard"))
        
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    uid, username = current_user()
    if uid is None:
        return redirect(url_for('login'))
    else:
        latest_attempt = data_manager.get_latest_user_record(uid)
        return render_template('dashboard.html', username=username, latest_attempt=latest_attempt)


@app.route('/history')
def history():
    uid, username = current_user()
    if uid is None:
        return redirect(url_for('login'))
    else:
        previous_attempts = data_manager.get_user_records(uid)
        return render_template('history.html', username=username, previous_attempts=previous_attempts)


@app.route('/result', methods=["GET", "POST"])
def result():
    uid, username = current_user()
    if uid is None:
        return redirect(url_for('login'))
    record_id = request.args.get('attempt_id')
    if record_id is None:
        return redirect(url_for('history'))
    
    # look through this user's own records for the one with the requested id
    choosen_attempt = None
    for record in data_manager.get_user_records(uid):
        if record.get_record_id() == record_id:
            choosen_attempt = record
            break

    # still None if the id is unknown or belongs to another user; results.html then says no results are available
    return render_template('results.html', choosen_attempt=choosen_attempt)


@app.route('/progress', methods=["GET", "POST"])
def progress():
    uid, username = current_user()
    if uid is None:
        error = "You must be logged in to access the progress page."
        return redirect(url_for('login'))
    else:
        # get the wanted data from the users previous attempts
        user_records = data_manager.get_user_records(uid)
        if len(user_records) > 1:
            history = data_manager.get_user_int_records(user_records, uid)[::-1]
        else:
            history = None
        return render_template('progress.html', history=history)


# route for settings
@app.route('/settings')
def settings():
    uid, username = current_user()
    if uid is None:
        return redirect(url_for('login'))
    return render_template('settings.html', username=username)

#route for updating username
@app.route('/update_username',  methods=["GET", "POST"])
def update_username():
    uid, username = current_user()
    if uid is None:
        return redirect(url_for('login'))
    if request.method == "GET":
        return redirect(url_for('settings'))
    result = io_manager.change_username(uid, request.form.get("username"))
    if not result.ok:
        return render_template("settings.html", error1=result.message, username=username)
    flash(result.message)
    return render_template("settings.html", username=result.username)


# route for password
@app.route('/update_password', methods=["GET", "POST"])
def update_password():
    uid, username = current_user()
    if uid is None:
        return redirect(url_for('login'))
    if request.method == "GET":
        return redirect(url_for('settings'))
    result = io_manager.change_password(uid, request.form.get("current"), request.form.get("newpw"),
                                        request.form.get("confirm"))
    if not result.ok:
        return render_template('settings.html', username=username, error2=[result.message])
    flash(result.message)
    return render_template('settings.html', username=username)


# route for deleting account
@app.route('/delete_account', methods=["POST"])
def delete_account():
    # get the current user id
    current_user_id = session.get('user_id')
    if not current_user_id:
        return redirect(url_for('login'))
    user = data_manager.get_user_by_id(current_user_id)
    if user is None:
        session.clear()
        return redirect(url_for('login'))
    # retrieve the user password and confirm text
    username = user.get_username()
    entered_password = request.form.get("delete_password", "")
    confirm_text = request.form.get("confirm_text", "").strip()
    errors = []
    # collect error messages
    if not entered_password:
        errors.append("Please enter your current password")
    elif not PasswordHasher().verify(entered_password, user.get_password()):
        errors.append("Incorrect password. Your account was not deleted.")
    if confirm_text != "DELETE":
        errors.append("Type DELETE in capital letters to confirm.")
    if errors:
        return render_template('settings.html', username=username, error3=errors)
    try:
        deleted = data_manager.delete_user(current_user_id)
    except Exception as error:
        print(f"Delete account error: {error}")
        deleted = False
    if not deleted:
        return render_template('settings.html', username=username,
                               error3=["There was an error deleting your account. Please try again later."])
    session.clear()
    flash("Your account has been deleted.")
    return redirect(url_for('main'))

@app.route('/wellness-check/<continue_chat>')
@app.route('/wellness-check')
def wellness_check(continue_chat=False):
    uid, username = current_user()
    if uid is None:
        return redirect(url_for('login'))
    # check if they have previous attempts
    # get todays date
    today_date = (date.today()).strftime("%d-%m-%Y")
    # get the date of the latest record
    latest_record = data_manager.get_latest_user_record(uid)
    done_today = latest_record is not None and latest_record.get_date() == today_date and not continue_chat

    if len(conversation.logs()) == 0 and not conversation.is_bot_typing():
        t = threading.Thread(target=get_AI_response, args=('Hello!',))
        t.start()
        conversation.set_bot_typing(True)

    return render_template('wellness-check.html', conversation=conversation, survey_results=None, already_done_today=done_today)

@app.get('/reset-conversation')
def reset_conversation():
    conversation = Conversation()
    return None

@app.route('/get', methods=['GET','POST'])
def chat():
    user_message = request.form["msg"]
    conversation.add_message('user', 'YT', user_message)
    conversation.set_bot_typing(True)

    return get_AI_response(user_message)

@app.route('/get-bot-response', methods=['GET'])
def wait_for_bot_response():
    while conversation.is_bot_typing():
        continue

    return conversation.get_last_log()
     
@app.route('/confirm-survey', methods=['GET'])
def confirm_survey():
    survey_results = ai_manager.show_survey_results(by_alias=True)

    return render_template('wellness-check.html', conversation=conversation, survey_results=survey_results)


@app.route('/submit_survey')
def submit_survey():
    uid, username = current_user()
    if uid is None:
        return redirect(url_for('login'))

    try:
        raw_answers = dict(ai_manager.show_survey_results())

    except (TypeError, ValidationError):    # no survey results yet, or they don't fit the chatbot's schema
        return redirect(url_for('wellness_check', continue_chat=True))
    
    #Run through io manager validation and return survey responses as object
    survey_result = io_manager.survey(uid, raw_answers)
    
    if not survey_result.result:    # an answer is invalid: the chatbot asks the user to fix it
        ai_manager.deny_survey()
        conversation.set_bot_typing(True)
        threading.Thread(target=get_AI_response,
                            args=(f"Some answers need to be fixed: {survey_result.message}",)).start()

        return redirect(url_for('wellness_check'))
    
    responses = survey_result.response
    user_input = responses.to_dict()
    
    try:
        ai_output = ai_manager.get_ai_output(user_input)
        if not ai_output.success:
            raise AssessmentFailed(f"The AI assessment failed: {ai_output.error}")
        ai_output = json.loads(ai_output.data)

        previous_attempts = data_manager.get_previous_attempts(uid)
        logic_output = logic_manager.to_dict(logic_manager.assess(responses, AIOutput(**ai_output), previous_attempts))

        # merge into one record and save it as today's (replacing any earlier one from today)
        assessment = data_manager.merge_record(user_input, ai_output, logic_output)
        # If cant be saved, raise error
        if not data_manager.replace_user_record(uid, assessment):
            raise AssessmentFailed("The assessment could not be saved.")

        # email the counsellor if the mental wellness or burnout score is over 80, crisis_alert is true,
        # counselling is recommended, or the route is Urgent support or Counsellor follow-up
        if logic_output["counselling_recommendation"]:
            if not io_manager.send_email(mail_recipient, username, assessment, mail):
                app.logger.error(f"Counsellor email could not be sent for user {uid}")

    except Exception as e:
        print(e)
        app.logger.exception("Assessment failed")
        conversation.add_message('ai', 'AI', "Sorry, I couldn't finish your assessment just now. "
                                       "Please press Yes to try again.")
        return redirect(url_for('confirm_survey'))    # shows the answers again with Yes / No

    conversation.reset_conversation()
    # redirect, so refreshing the results page doesn't run the assessment (and the email) again
    return redirect(url_for('result', attempt_id=data_manager.get_latest_user_record(uid).get_record_id()))

@app.route('/deny-survey')
def deny_survey():
    ai_manager.deny_survey()
    threading.Thread(target=get_AI_response, args=('The survey results are not accurate.',)).start()
    conversation.set_bot_typing(True)

    return redirect(url_for('wellness_check', continue_chat=True))


def get_AI_response(text, start_chat=False):
    if start_chat:
        bot_response = ai_manager.start_conversation()
    else:
        bot_response = ai_manager.prompt_bot(text)

    conversation.add_message('ai', 'AI', bot_response['text'])
    conversation.set_bot_typing(False)

    return bot_response


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main'))


# add 404 page so that there is some error handling
@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/error_404.html")