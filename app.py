import re
import os
import threading
import sys
import markdown

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from dotenv import load_dotenv
from markupsafe import escape
from ai_manager import AIManager
from data_manager import DataManager
from io_helpers.hasher import PasswordHasher
from io_helpers.validators import username_errors, password_errors
from ai_manager_helper.data_classes.conversation import Conversation
from ai_manager_helper.data_classes.survey_entity_schema import SurveyEntitySchema

ai_manager = AIManager()
ai_manager.connect_client()
data_manager = DataManager()

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

        data_manager.close()
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
        previous_attempts = data_manager.get_previous_attempts(current_user_id)
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
            return render_template("settings.html", success=success_message, username = updated_username)
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
            return render_template('settings.html', username=current_username, success2=success_message)
        else:
            error.append("There has been an issue with updating your password, try again later")
            if len(error)>0:
                return render_template('settings.html', username=current_username, error2 = error)
        # updates = {"username" : new_username}
        # success = data_manager.update_user(current_user_id, updates)
    return render_template('settings.html', username = current_username)



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
    conversation.set_done(True)
    survey_results = ai_manager.show_survey_results()

    return redirect(url_for('progress'))

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