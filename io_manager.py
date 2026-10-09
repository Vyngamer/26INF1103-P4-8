'''
INPUT LOGIC
'''

#Generic integer input function with range validation
def int_range_input(prompt: str, minimum: int, maximum: int) -> int:
	while True:
		#Integer validation
		try:
			value = int(input(prompt).strip())
		except ValueError:
			print("Please enter a whole number.")
			continue
        #Range validation
		if minimum <= value <= maximum:
			return value
		print(f"Please enter a number from {minimum} to {maximum}.")

#Prompt for avg daily sleep hours in the past week(0-24)
def get_sleep_duration() -> int:
	return int_range_input("How many hours per day did you sleep on average for the past week?: ", 0, 24)

#Prompt for stress level on a scale of 1-10
def get_stress_level() -> int:
    return int_range_input("On a scale of 1-10, how stressed have you been for the past week?: ", 1, 10)

#Prompt for focus level on a scale of 1-10
def get_focus_level() -> int:
    return int_range_input("On a scale of 1-10, how focused have you been for the past week?: ", 1, 10)

#Prompt for academic workload level on a scale of 1-10
def get_workload_level() -> int:
	return int_range_input("On a scale of 1-10, how heavy has your academic workload been for the past week?: ", 1, 10)

#Prompt for social activity level on a scale of 1-10
def get_social_activity_level() -> int:
    return int_range_input("On a scale of 1-10, how socially active have you been for the past week?: ", 1, 10)

#mood options
mood_options = ("Motivated", "Calm", "Anxious", "Sad", "Exhausted")

#Prompt for mood selection from predefined options
def get_mood() -> str:
    #List out options
    print("Select your mood from the following options:")
    for i, mood in enumerate(mood_options, start=1):
        print(f"{i}. {mood}")
    #Input validation loop
    while True:
        try:
            choice = int(input("Enter the number corresponding to your mood: ").strip())
            if 1 <= choice <= len(mood_options):
                return mood_options[choice - 1]
            else:
                print(f"Please enter a number from 1 to {len(mood_options)}.")
        except ValueError:
            print("Please enter a valid number.")

#Prompt for a free-response reflection
def get_reflection(limit: int = 500) -> str:
	while True:
		reflection = input("Reflection: ").strip()
		if reflection:
			if limit is not None and len(reflection) > limit:
				print(f"Please enter a reflection with at most {limit} characters.")
				continue
			return reflection
		print("Please enter a reflection.")

#Note to self: consider allowing empty reflection


#Dictionary of questions
questionnaire = {
    "sleep_duration": get_sleep_duration,
    "stress_level": get_stress_level,
    "focus_level": get_focus_level,
    "academic_workload": get_workload_level,
    "mood": get_mood,
    "social_activity_level": get_social_activity_level,
    "reflection": get_reflection
}

#Prompt all questions in the questionnaire and return a dictionary of responses
def prompt_questionnaire() -> dict:
    responses = {}
    for i, (question, func) in enumerate(questionnaire.items(), start=1):
        print(f"{i}. {question.replace('_', ' ').title()}")
        responses[question] = func()
    return responses

#test
print(prompt_questionnaire())

'''
OUTPUT LOGIC
'''

#placeholder for ai output
ai_sample = {
      "mental_wellness_risk_score": 78,
      "sentiment": "Negative",
      "burnout_risk_score": 82,
      "crisis_alert": False,
      "primary_stressor": "Assignment Deadlines",
      "personalized_recommendations": "Prioritize sleep and manage deadlines."
}

#placeholder for logic output
logic_sample = {
      "risk_tier": "High",
      "warnings": ["Burnout Warning", "warning 2"],
      "route": "Counselor follow-up",
      "needs_counseling": True
}

#Output AI and logic results to the user
def risk_assessment():
    print("\n--- Mental Health Assessment Results ---")
    #AI risk score & risk tier
    print(f"Mental Wellness Risk Score: {ai_sample['mental_wellness_risk_score']} / 100 ({logic_sample['risk_tier']} Risk)")
    #Burnout risk score
    print(f"Burnout Risk Score: {ai_sample['burnout_risk_score']} / 100")
    #Sentiment of reflection
    #print(f"Sentiment: {ai_sample['sentiment']}")
    #Primary stressors
    print(f"Primary Stressor: {ai_sample['primary_stressor']}")
    #Note to self: Check if there may be multiple stressors

    #Recommendations
    print(f"\nRecommendation(s):\n{ai_sample['personalized_recommendations']}")
    
    #Warnings & Crisis Alert
    print(f"\nPlease heed these warning(s):\n{'\n'.join(logic_sample['warnings'])}")
    #print(f"Crisis Alert: {'YES' if ai_sample['crisis_alert'] else 'NO'}")

    #Suggest counseling if needed
    if logic_sample['needs_counseling']:
        print(f"\nAlert:You are advised to seek counseling.")

#Note to self: implement rich text after logic flow is working
    

#Run Output
risk_assessment()