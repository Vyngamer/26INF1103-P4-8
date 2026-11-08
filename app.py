import re
import os

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
from markupsafe import escape
from ai_manager import AIManager
from data_manager import DataManager
from io_helpers.hasher import PasswordHasher
from io_helpers.validators import username_errors, password_errors

ai_manager = AIManager()
ai_manager.connect_client()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

previous_attempt = {
    "record_id": "3d26c70e-8056-4332-a5c1-6a303d7ac992",
    "date": "17-10-2026",
    "time": "13:46:19",
    "user_input": {
        "user_id": "69182f01-0c95-496e-8c90-34c5cbd3bcb2",
        "sleep_duration": 6.0,
        "stress_level": 9,
        "focus_level": 5,
        "academic_workload": 9,
        "mood": "Exhausted",
        "social_activity_level": 4,
        "reflection": "I am really exhausted and sad and lonely"
    },
    "ai_output": {
        "burnout_risk_score": 78,
        "crisis_alert": False,
        "mental_wellness_risk_score": 75,
        "personalized_recommendations": "It sounds like you are carrying a heavy burden right now, and it is completely valid to feel exhausted. Please prioritize getting an extra hour of restorative sleep tonight and try to reach out to one trusted friend or family member, as social connection can be a powerful antidote to feelings of loneliness.",
        "primary_stressor": "Academic Workload",
        "sentiment": "Negative"
    },
    "logic_output": {
        "mental_wellness_risk_tier": "High",
        "warnings": [

            "Cognitive Fatigue Risk"
        ],
        "route": "Counsellor follow-up",
        "counselling_recommendation": True,
        "display_messages": [
            "You slept less than 7 hours. Try to get more sleep.",
            "You slept 0.50 hours more than your average.",
            "Your social activity has dropped across four consecutive attempts. Try connecting with others.",
            "Your focus level has improved since your last attempt. Keep it up!",
            "Your burnout risk score has improved since your last attempt. Keep it up!"
        ]
    }
}

user_details = {
    "user_id": "69182f01-0c95-496e-8c90-34c5cbd3bcb2",
    "username": "user3"
}

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

        # connect to the database
        data_manager = DataManager()

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

        # connect to the database
        data_manager = DataManager()

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
        data_manager = DataManager()
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
        data_manager = DataManager()
        username = data_manager.get_user_by_id(current_user_id)
        previous_attempts = data_manager.get_previous_attempts(current_user_id)
        print(previous_attempts)
    return render_template('history.html', username=username.get_username(), previous_attempts=previous_attempts)


@app.route('/wellness-check')
def wellness_check():
    return render_template('wellness-check.html')

@app.route('/get', methods=['GET','POST'])
def chat():
    user_message = request.form["msg"]

    return get_AI_response(user_message)


def get_AI_response(text):

    # clean text here

    print(text)
    return ai_manager.prompt_bot(text)
