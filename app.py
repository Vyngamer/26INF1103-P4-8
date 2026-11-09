import re
import os

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
from markupsafe import escape
from ai_manager import AIManager
from data_manager import DataManager
from io_helpers.hasher import PasswordHasher
from io_helpers.validators import username_errors, password_errors
from ai_manager_helper.data_classes.conversation import Conversation
import threading
import sys

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
        return render_template("login.html", error=error)
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
        return render_template("login.html", error=error)
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
        return render_template("login.html", error=error)
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


@app.route('/wellness-check')
def wellness_check():
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
     
def get_AI_response(text):
    bot_response = ai_manager.prompt_bot(text)
    conversation.add_message('ai', bot_response)
    conversation.set_bot_typing(False)

    return bot_response

