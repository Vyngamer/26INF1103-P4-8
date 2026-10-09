import json

'''
INPUT
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

#Generic float input function with range validation
def float_range_input(prompt: str, minimum: float, maximum: float) -> float:
	while True:
		#Float validation
		try:
			value = float(input(prompt).strip())
		except ValueError:
			print("Please enter a valid number.")
			continue
		#Range validation
		if minimum <= value <= maximum:
			return value
		print(f"Please enter a number from {minimum} to {maximum}.")

#Prompt for avg daily sleep hours in the past week(0-24)
def get_sleep_duration() -> float:
	return float_range_input("How many hours per day did you sleep on average for the past week?: ", 0, 24)

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

#Prompt for mood selection from predefined options
def get_mood() -> str:
    #mood options
    mood_options = ("Motivated", "Calm", "Anxious", "Sad", "Exhausted")
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


#Prompt all questions in the questionnaire and return a dictionary of responses
def prompt_questionnaire() -> dict:
    #Dictionary of question functions
    questionnaire = {
        "sleep_duration": get_sleep_duration,
        "stress_level": get_stress_level,
        "focus_level": get_focus_level,
        "academic_workload": get_workload_level,
        "mood": get_mood,
        "social_activity_level": get_social_activity_level,
        "reflection": get_reflection
    }
    responses = {}
    for i, (question, func) in enumerate(questionnaire.items(), start=1):
        print(f"\n{i}. {question.replace('_', ' ').title()}")
        responses[question] = func()
    return responses

'''
OUTPUT LOGIC
'''

#Output AI and logic results to the user
def risk_assessment(results):
    print("\n--- Mental Health Assessment Results ---")
    #AI risk score & risk tier
    print(f"Mental Wellness Risk Score: {results['mental_wellness_risk_score']} / 100 ({results['risk_tier']} Risk)")
    #Burnout risk score
    print(f"Burnout Risk Score: {results['burnout_risk_score']} / 100")
    #Sentiment of reflection
    #print(f"Sentiment: {results['sentiment']}")
    #Primary stressors
    print(f"Primary Stressor: {results['primary_stressor']}")
    #Note to self: Check if there may be multiple stressors

    #Recommendations
    print(f"\nRecommendation(s):\n{results['personalized_recommendations']}\n")
    
    #Warnings & Crisis Alert
    print(f"Please heed these warning(s):\n{'\n'.join(results['warnings'])}\n")
    #print(f"Crisis Alert: {'YES' if ai_sample['crisis_alert'] else 'NO'}")

    #Suggest counseling if needed
    if results['needs_counseling']:
        print(f"Alert:You are advised to seek counseling.\n")

#Note to self: implement rich text after logic flow is working

'''
File I/O
'''

#Save results to json
def save_results(filename, results):
    with open(filename, 'w') as file:
        json.dump(results, file, indent=2)

#Load from json
def load_results(filename):
    try:
        with open(filename, 'r') as file:
            res = json.load(file)
    #Empty list if file not found
    except FileNotFoundError or json.JSONDecodeError:
        res = []
    return res


#Function to start survey & return results
def full_survey(files=["","",""]):
    survey = prompt_questionnaire()   #Start survey
    save_results(files[0],survey) #Save results to JSON file
    
    #Get logic and AI outputs
    logic_output = load_results(files[1])
    ai_output = load_results(files[2])
    result = logic_output | ai_output   #Merge into one dict

    input("\nPress Enter to Continue... ")
    return risk_assessment(result)