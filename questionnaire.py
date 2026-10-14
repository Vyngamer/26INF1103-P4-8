'''
Survey Questions and File I/O
'''

import json, sys
from prompts import prompt_range, prompt_choice, prompt_text

'''
INPUT
'''

#Prompt for avg daily sleep hours in the past week(0-24)
def get_sleep_duration() -> float:
	return prompt_range("How many hours per day did you sleep on average for the past week?: ", 0, 24, cast=float)

#Generic 1-10 numerical scale question builder
def scale_question(description: str):
    prompt = f"On a scale of 1-10, {description} for the past week?: "
    return lambda: prompt_range(prompt, 1, 10)

#Prompt for mood selection from predefined options
MOOD_OPTIONS = ["Motivated", "Calm", "Anxious", "Sad", "Exhausted"]
def get_mood() -> str:
    return prompt_choice(MOOD_OPTIONS,
                         "Select your mood from the following options:",
                         "Enter the number corresponding to your mood: ")

#Prompt for a free-response reflection
def get_reflection(limit: int = 500) -> str:
    while True:
        reflection = prompt_text("Reflection: ")
        if len(reflection) <= limit:
            return reflection
        print(f"Please enter a reflection with at most {limit} characters.")

#Prompt all questions in the questionnaire and return a dictionary of responses
def prompt_questionnaire() -> dict:
    #Dictionary of question functions
    questionnaire = {
        "sleep_duration": get_sleep_duration,
        "stress_level": scale_question("how stressed have you been"),
        "focus_level": scale_question("how focused have you been"),
        "academic_workload": scale_question("how heavy has your academic workload been"),
        "mood": get_mood,
        "social_activity_level": scale_question("how socially active have you been"),
        "reflection": get_reflection
    }
    responses = {
        "user_id": None
    }
    try:
        for i, (question, func) in enumerate(questionnaire.items(), start=1):
            print(f"\n{i}. {question.replace('_', ' ').title()}")
            responses[question] = func()
        return responses
    except (KeyboardInterrupt, EOFError):
            print("\n\nSurvey cancelled.")
            return None

'''
OUTPUT LOGIC
'''

#Output AI and logic results to the user
def risk_assessment(results: dict) -> None:
    print("\n--- Mental Health Assessment Results ---")
    #AI risk score & risk tier
    print(f"Mental Wellness Risk Score: {results.get('mental_wellness_risk_score', 'N/A')} / 100 "
          f"({results.get('mental_wellness_risk_tier', 'Unknown')} Risk)")
    #Burnout risk score
    print(f"Burnout Risk Score: {results.get('burnout_risk_score', 'N/A')} / 100")
    #Primary stressors
    print(f"Primary Stressor: {results.get('primary_stressor', 'N/A')}")
    #Note to self: Check if there may be multiple stressors

    #Recommendations
    print(f"\nRecommendation(s):\n{results.get('personalized_recommendations', 'None')}\n")

    #Warnings
    warnings = results.get("warnings", [])
    if warnings:
        print("Please heed these warning(s):")
        print("\n".join(warnings))
        print()

    #Crisis alert
    if results.get("crisis_alert"):
        print("!! You may be in crisis. Please contact a crisis helpline or emergency services now,")
        print("   or reach out to someone you trust. You do not have to go through this alone.\n")

    #Suggest counseling if needed
    if results.get("counselling_recommendation"):
        print("Alert: You are advised to seek counseling.\n")

#Note to self: implement rich text after logic flow is working

'''
File I/O
'''
'''
#Save results to json
def save_results(filename: str, results: dict) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)
'''
#Load from json
def load_results(filename: str) -> dict:
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}