import re
import os
import threading
import sys
import markdown
import logic_manager
import json

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from dotenv import load_dotenv
from markupsafe import escape
from ai_manager import AIManager
from data_manager import DataManager
from io_helpers.hasher import PasswordHasher
from io_helpers.user_input import UserInput
from io_helpers.validators import username_errors, password_errors
from ai_manager_helper.data_classes.conversation import Conversation
from ai_manager_helper.data_classes.survey_entity_schema import SurveyEntitySchema
from ai_manager_helper.api_client_classes.gemini_client import GeminiClient
from ai_manager_helper.data_classes.ai_output import AIOutput
from logic_manager_helper.LogicManager import LogicManager

ai_manager = AIManager()
ai_manager.connect_client()
data_manager = DataManager()
logic_manager = LogicManager()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

conversation = Conversation()

# route for index, this will be the default page when the app runs
@app.route("/")
def main():
    return render_template("index.html")

# route for register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # get the form details
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm")

        # check if the passwords match
        if password != confirm_password:
            error = "Passwords do not match."
            return render_template("register.html", error=error)

        # check if the username and password meet the requirements
        username_problems = username_errors(username)
        password_problems = password_errors(password)
        print(f"Username problems: {username_problems}, Password problems: {password_problems}")
        if username_problems or password_problems:
            error = " ".join(username_problems + password_problems)
            return render_template("register.html", error=error)

        # check if the username already exists
        if data_manager.get_user_by_username(username) is not None:
            error = "Username already exists. Please choose another."
            return render_template("register.html", error=error)

        # if the username is ok, store the user
        password_hash = PasswordHasher().hash(password)
        try:
            user_id = data_manager.create_user(username, password_hash)
            if user_id is None:
                error = "Could not create your account. Please try again."
                return render_template("register.html", error=error)
        except (ConnectionError, ValueError) as e:
            error = "Unable to connect to the database. Please try again later."
            return render_template("register.html", error=error)
        flash("Account Created Successfully!!")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # get the form details
        username = request.form.get("username")
        password = request.form.get("password")

        # set a flag for login
        can_login = True

        # check if the username exists
        user = data_manager.get_user_by_username(username)
        if user is None:
            can_login = False
            error = "Invalid username or password."
            return render_template("login.html", error=error)

        # check if the password is correct
        password_hash = user.get_password()
        if not PasswordHasher().verify(password, password_hash):
            can_login = False
            error = "Invalid username or password."
            return render_template("login.html", error=error)

        if can_login:
            session['user_id'] = user.get_user_id()
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    current_user_id = session.get('user_id')
    if not current_user_id:
        error = "You must be logged in to access the dashboard."
        return redirect(url_for('login'))
    else:
        # get current user past attempts from the database
        username = data_manager.get_user_by_id(current_user_id)
        latest_attempt = data_manager.get_latest_user_record(current_user_id)
        # check if there are any previous attempts
        if not latest_attempt:
            latest_attempt = None
        return render_template('dashboard.html', username=username.get_username(), latest_attempt = latest_attempt)

@app.route('/history')
def history():
    current_user_id = session.get('user_id')
    if not current_user_id:
        error = "You must be logged in to access the history page."
        return redirect(url_for('login'))
    else:
        # get current user past attempts from the database
        username = data_manager.get_user_by_id(current_user_id)
        #previous_attempts = data_manager.get_previous_attempts(current_user_id)
        previous_attempts = data_manager.get_user_records(current_user_id)
    return render_template('history.html', username=username.get_username(), previous_attempts=previous_attempts)


@app.route('/result', methods=["GET", "POST"])
def result():
    current_user_id = session.get('user_id')
    if not current_user_id:
        error = "You must be logged in to access the results page."
        return redirect(url_for('login'))
    else:
        # get the id of the wanted attempt
        current_record_id = request.args.get('attempt_id')
        if current_record_id is None:
            error = "No attempt ID provided."
            return render_template("history.html", error=error)
        else:
            # get current user past attempts from the database
            user_previous_attempts = data_manager.get_user_records(current_user_id)
            choosen_attempt = None
            for previous_attempt in user_previous_attempts:
                if previous_attempt.get_record_id() == current_record_id:
                    choosen_attempt = previous_attempt
                    break
            if not choosen_attempt:
                choosen_attempt = None
        return render_template('results.html', choosen_attempt=choosen_attempt)

@app.route('/progress', methods=["GET", "POST"])
def progress():
    current_user_id = session.get('user_id')
    if not current_user_id:
        error = "You must be logged in to access the progress page."
        return redirect(url_for('login'))
    else:
        # get the wanted data from the users previous attempts
        all_records = data_manager.load_records()
        wanted_data = data_manager.get_user_int_records(all_records, current_user_id)
        print(len(wanted_data))
        if wanted_data is None:
            wanted_data = None
        if len(wanted_data) < 2:
            wanted_data = None
        return render_template('progress.html', history=wanted_data, )


# route for settings
@app.route('/settings')
def settings():
    current_user_id = session.get('user_id')
    if not current_user_id:
        error = "You must be logged in to access the settings page"
        return redirect(url_for('login'))
    else:
        current_username = data_manager.get_user_by_id(current_user_id).get_username()
        if current_username is None:
            current_username = None
        return render_template('settings.html', username = current_username)

#route for updating username
@app.route('/update_username',  methods=["GET", "POST"])
def update_username():
    # get current user id
    current_user_id = session.get('user_id')
    # get current username
    current_username = data_manager.get_user_by_id(current_user_id).get_username()
    # get the thing that the user enters
    new_username = request.form.get("username").strip()
    if not new_username:
        error = "Please Enter a username"
        return render_template("settings.html", error1=error, username = current_username)
    if data_manager.get_user_by_username(new_username) is not None:
        error = "Username already exists. Please choose another."
        return render_template("settings.html", error1=error, username = current_username)
    else:
        updates = {"username" : new_username}
        success = data_manager.update_user(current_user_id, updates)
        if success:
            success_message = "Your Usesrname has been successfully updated"
            updated_username = data_manager.get_user_by_id(current_user_id).get_username()
            flash(success_message)
            return render_template("settings.html", username = updated_username)
        else:
            error = "There was an error with updating your username"
            return render_template("settings.html", error = error, username = current_username)


# route for password
@app.route('/update_password', methods=["GET", "POST"])
def update_password():
    # get current user id
    current_user_id = session.get('user_id')
    current_username = data_manager.get_user_by_id(current_user_id).get_username()
    # get the current password, new password and confirm new password that the user entered
    entered_current_password = request.form.get("current")
    entered_new_password = request.form.get("newpw")
    entered_confirm_new_password = request.form.get("confirm")
    # check if each is empty
    error = []
    if not entered_current_password:
        error.append("Please enter your old password")
    if not entered_new_password:
        error.append("Please enter your new password")
    if not entered_confirm_new_password:
        error.append("Please enter your confirm new password")
    if len(error) > 0:
        return render_template('settings.html', username=current_username, error2 = error)
    
    # get the current password
    current_password = data_manager.get_user_by_id(current_user_id).get_password()
    password_check = PasswordHasher().verify(entered_current_password, current_password)
    if not password_check:
        error.append("The current password you entered does not match your current password, Please try again")
        if len(error)>0:
            return render_template('settings.html', username=current_username, error2 = error)

    # check if new pass and confirm new pass is same
    match = True
    if entered_new_password != entered_confirm_new_password:
        match = False
        error.append("Your new password and confirm new password does not match")
        if len(error)>0:
            return render_template('settings.html', username=current_username, error2 = error)

    # do the proper changing of password
    if password_check and match:
        updates = {"password": PasswordHasher().hash(entered_new_password)}
        success = data_manager.update_user(current_user_id, updates)
        if success:
            success_message = "Your Password has been successfully updated!"
            flash(success_message)
            return render_template('settings.html', username=current_username)
        else:
            error.append("There has been an issue with updating your password, try again later")
            if len(error)>0:
                return render_template('settings.html', username=current_username, error2 = error)
        # updates = {"username" : new_username}
        # success = data_manager.update_user(current_user_id, updates)
    return render_template('settings.html', username = current_username)

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

@app.route('/wellness-check')
def wellness_check():
    if len(conversation.logs()) == 0 and not conversation.is_bot_typing():
        t = threading.Thread(target=get_AI_response, args=('Hello!',))
        t.start()
        conversation.set_bot_typing(True)

    return render_template('wellness-check.html', conversation=conversation)

@app.route('/get', methods=['GET','POST'])
def chat():
    user_message = request.form["msg"]
    conversation.add_message('user', user_message)
    conversation.set_bot_typing(True)

    return get_AI_response(user_message)

@app.route('/get-bot-response', methods=['GET'])
def wait_for_bot_response():
    while conversation.is_bot_typing():
        continue

    return conversation.get_last_log()
     
@app.route('/confirm-survey', methods=['GET'])
def confirm_survey():
    survey_results = ai_manager.show_survey_results()
    html_output = '<p>Are all of these fields correct?</p>'

    for key, value in survey_results:
        html_output += '<p>' + key + ': ' + str(value) + '</p>'

    flash(html_output)
    return redirect(url_for('wellness_check'))

@app.route('/submit_survey')
def submit_survey():
    current_user_id = session.get('user_id')
    if not current_user_id:
        return redirect(url_for('login'))
    else:
        conversation.set_done(True)
        user_input = ai_manager.show_survey_results()
        assessor = GeminiClient(
            "gemini-3.5-flash-lite",
            system_instruction="""
                You are an expert student counselor and psychological assessment AI specializing in adolescent and higher education mental health.

                Your job is to analyze quantitative student wellness metrics alongside qualitative reflection text to produce a structured JSON mental health assessment.

                Only answer questions related to the user's mental health.

                ### INPUT DATA DEFINITIONS

                - Sleep Duration: Average daily sleep hours over the past week (0-24). The user had {sleep} hours of sleep.
                - Stress Level: Current stress (1 = Very Low, 10 = Very High). The user's stress level is {stress} out of 10.
                - Focus Level: Ability to concentrate (1 = Very Poor, 10 = Excellent). The user's focus level is {focus} out of 10.
                - Academic Workload: Coursework load (1 = Light, 10 = Very Heavy). The user's academic workload is {workload} out of 10.
                - Mood for the Day: Emotional state ["Motivated", "Calm", "Anxious", "Sad", "Exhausted"]. The user's mood is {mood}.
                - Social Activity Level: Engagement level (1 = Isolated, 10 = Very Social). The user's social activity level is {social} out of 10.
                - Reflection: Free-response text capturing personal thoughts and concerns. The user's reflection text is {reflection}.

                ### EVALUATION & SCORING RUBRIC

                1. Mental Wellness Risk Score (0-100):
                - Baseline calculation: Aggregate high stress, low focus, poor sleep (<6 hours), low social activity (<=3), and negative mood ("Anxious", "Sad", "Exhausted").
                - Qualitative Adjustment: Analyze the reflection text.
                    - Expressing hopelessness, feeling overwhelmed, or severe anxiety increases the score by +15 to +30 points.
                    - Neutral or constructive reflection keeps the baseline score intact.
                    - Expressing positive coping mechanisms or a calm mindset decreases the score by -10 to -20 points.
                - Scale: 0-40 (Low Risk), 41-70 (Medium Risk), 71-100 (High Risk).

                2. Burnout Risk Score (0-100):
                - Heavily weight the interaction between Academic Workload (>=7), Sleep Duration (<6h), Focus Level (<=2), and Mood ("Exhausted" or "Anxious").
                - High Workload + Low Sleep + Low Focus = Automatic score >70.
                - High Workload balanced by High Sleep and High Social Activity = Moderate score (40-60).

                3. Crisis Alert (Boolean: true/false):
                - MUST BE true IF AND ONLY IF:
                    - Reflection text contains thoughts or explicit mentions of self-harm, suicidal ideation, feeling completely hopeless or giving up on life, feeling unsafe, or extreme mental breakdowns.
                    - OR Mental Wellness Risk Score is extremely high (>=85) with social activity = 1 and severe sleep deprivation (<4 hours).
                - Otherwise MUST BE false.

                4. Sentiment Analysis (Strictly one of: "Positive", "Neutral", "Negative"):
                - Primary basis: The reflection text combined with emotional mood state.
                - "Exhausted", "Anxious", or "Sad" with distressed reflection = "Negative".
                - "Motivated" or "Calm" with positive reflection = "Positive".
                - Balanced or matter-of-fact reflections = "Neutral".

                5. Primary Stressor (1-3 Words):
                - Summarize the single greatest contributor to their current state.
                - Examples: "Academic Workload", "Sleep Deprivation", "Social Isolation", "Exam Anxiety", "Time Management".

                6. Personalized Recommendations (String):
                - Provide a concise (2-3 sentences), warm, empathetic, and actionable wellness suggestion.
                - Tailor recommendations directly to the user's specific metrics.
                - For example, if sleep <5 hours, focus on improving sleep habits before tackling workload.

                """,
            response_json_format={
                "type": "object",
                "properties": {
                    "mental_wellness_risk_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "burnout_risk_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "sentiment": {
                        "type": "string",
                        "enum": ["Positive", "Neutral", "Negative"]
                    },
                    "crisis_alert": {
                        "type": "boolean"
                    },
                    "primary_stressor": {
                        "type": "string"
                    },
                    "personalized_recommendations": {
                        "type": "string"
                    }
                },
                "required": [
                    "mental_wellness_risk_score",
                    "burnout_risk_score",
                    "sentiment",
                    "crisis_alert",
                    "primary_stressor",
                    "personalized_recommendations"]})
        assessor.connect_client()
        result = assessor.call_api(user_input.model_dump_json(exclude={"text", "survey_done"}))
        ai_output = json.loads(result.data)
        dict_user_input = user_input.model_dump()
        dict_user_input = {"user_id": current_user_id, **dict_user_input}

        # get the user input and ai output as an object
        user_input_obj = UserInput(**dict_user_input)
        ai_output_obj = AIOutput(**ai_output)

        # get the previous attempts
        previous_attempts = data_manager.get_previous_attempts(current_user_id)

        # get the logic output
        logic_output = logic_manager.assess(user_input_obj, ai_output_obj, previous_attempts)

        # merge records into 1
        assessment = data_manager.merge_record(dict_user_input, ai_output, logic_manager.to_dict(logic_output))
        # save to db
        success = data_manager.replace_user_record(current_user_id, assessment)
        # latest_assessment = data_manager.get_latest_user_record(current_user_id)
        # latest_assessment_id = latest_assessment.get_record_id()
        # latest_assessment_id = data_manager.get_latest_user_record(current_user_id).get_record_id()
        # print(latest_assessment_id)
        # choosen_attempt = None
        # for previous_attempt in previous_attempts:
        #     if previous_attempt.get_record_id() == latest_assessment_id:
        #         choosen_attempt = previous_attempt
        #         break
        #     if not choosen_attempt:
        #         choosen_attempt = None
        #     print(type(choosen_attempt))
        # get the ID of the new record
        latest_assessment_id = data_manager.get_latest_user_record(current_user_id).get_record_id()
        # load everything the user has
        user_records = data_manager.get_user_records(current_user_id)
        print(latest_assessment_id)
        for user_record in user_records:
            if user_record.get_record_id() == latest_assessment_id:
                choosen_attempt = user_record
        return render_template('results.html', choosen_attempt=choosen_attempt)

@app.route('/deny-survey')
def deny_survey():
    ai_manager.deny_survey()
    threading.Thread(target=get_AI_response, args=('The survey results are not accurate.',)).start()
    conversation.set_bot_typing(True)

    return redirect(url_for('wellness_check'))

def get_AI_response(text):
    bot_response = ai_manager.prompt_bot(text)
    conversation.add_message('ai', bot_response['text'])
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