from flask import Flask, render_template, request, jsonify
from markupsafe import escape
from ai_manager import AIManager

ai_manager = AIManager()
ai_manager.connect_client()

app = Flask(__name__)

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

@app.route("/")
def index():
    return render_template('dashboard.html', user_details=user_details, previous_attempt=previous_attempt)

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

