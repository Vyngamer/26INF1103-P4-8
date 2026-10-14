from google import genai
import sys
import os
import json
import google
from google.genai._gaos.lib.compat_errors import APIConnectionError, NotFoundError


backup_model = "gemini-3.5-flash-lite"
primary_model = "gemini-3.1-flash-lite"


# decorator which handles general errors after all other error handlers
def general_error_handler(base_api_call_func):
    def catch_general_error(*args, **kwargs):
        try:
            return base_api_call_func(*args, **kwargs)
        except Exception as e:
            print("No AI functionality.")
            raise e

    return catch_general_error

# decorator to handle other errors
def backup_model_retry(base_api_call_func):
    def retry_api_call(*args, **kwargs):
        try: 
            return base_api_call_func(*args, **kwargs)
        except NotFoundError as e:
            print("An error occured.")
            print("Retrying with secondary model...")

            try:
                kwargs['model'] = backup_model
                return base_api_call_func(*args, **kwargs)
            except NotFoundError as e: 
                print("Both models unavailable.")
                raise e
    
    return retry_api_call

# decorator to handle network failure
def failed_network_handler(base_api_call_func):
    def failed_network_notice(*args, **kwargs):
        try:
            return base_api_call_func(*args, **kwargs)
        except APIConnectionError as e:

            print("Network connection error. Please check that you are connected to the internet.")
            raise e
    return failed_network_notice

# decorator for when the primary api key fails
def failed_api_key_handler(base_api_call_func):
    def api_key_fallback(*args, **kwargs):
        try:
            return base_api_call_func(*args, **kwargs)    
        except ValueError as e:
            print("Primary key failed... Switching to alternate key")
            
            os.environ["GEMINI_API_KEY"] = os.getenv("BACKUP_GEMINI_API_KEY")
            try:
                return base_api_call_func(*args, **kwargs) 
            except ValueError as e:
                print("Both API keys unavailable...")
                raise e
        
    return api_key_fallback

# @error_exit_program
@general_error_handler
@failed_api_key_handler
def connect_client():
    return genai.Client()

# @error_exit_program
@general_error_handler
@backup_model_retry
@failed_api_key_handler
@failed_network_handler
def call_api(prompt, system_instruction, response_output_format, previous_interaction_id, model=primary_model):
    """
    The function returns the interaction object which contains the response from the chatbot.

    Parameters
    ---
    prompt: str
        input from the user that will prompt the chatbot
    system_instruction: str
        a message that tells the chatbot what it should be
    previous_interaction_id (optional): str
        allows for continuation of the conversation
    response_output_format: dict
        follows the pydantic model json schema format that tells the chatbot the format of the json response 

    Returns
    ---
    interaction: Obj
        contains the interactions.output_text property which is the response from the chosen chatbot
        contains the interactions.id property which shows the interaction id for stateful conversations.
    """

    interaction = client.interactions.create(
        model=model,
        input=prompt,
        system_instruction=system_instruction,
        previous_interaction_id=previous_interaction_id,
        response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": response_output_format
    })

    return interaction

def generate_prompt(survey_data):
    """
    Generates a prompt for the chatbot at the start of the program.
     
    Parameters
    ---
    survey_data: dict
        a python dictionary containing data from the user on the survey
    
    Returns
    ---
    survey_instruction: str
        a message that tells the chatbot what it should be
    prompt:
        contains the survey data for the AI to analyse
    """
    
    system_instruction="""
        You are an expert student counselor and psychological assessment AI specializing in adolescent and higher education mental health. Your job is to analyze quantitative student wellness metrics alongside qualitative reflection text to produce a structured JSON mental health assessment. Only answer questions related to the user's mental health.

        ### INPUT DATA DEFINITIONS
        - Sleep Duration: Average daily sleep hours over past week (0-24), The user had {sleep} hours of sleep
        - Stress Level: Current stress (1 = Very Low, 10 = Very High), the user's stress level is {stress} out of 10
        - Focus Level: Ability to concentrate (1 = Very Poor, 5 = Excellent), the user's focus level is {focus} out of 10
        - Academic Workload: Coursework load (1 = Light, 10 = Very Heavy), the user's academic workload is {workload} out of 10
        - Mood for the Day: Emotional state ["Motivated", "Calm", "Anxious", "Sad", "Exhausted"], the user's mood is {mood}
        - Social Activity Level: Engagement level (1 = Isolated, 10 = Very Social), the user's social activity level is {social} out of 10
        - Reflection: Free-response text capturing personal thoughts/concerns, the user's reflection text is {reflection}.

        ### EVALUATION & SCORING RUBRIC
        1. Mental Wellness Risk Score (0 - 100):
        - Baseline calculation: Aggregate high stress, low focus, poor sleep (<6 hours), low social activity (≤3), and negative mood ("Anxious", "Sad", "Exhausted").
        - Qualitative Adjustment: Analyze the reflection text.
            * Expressing hopelessness, feeling overwhelmed, or severe anxiety increases the score by +15 to +30 points.
            * Neutral/constructive reflection keeps baseline score intact.
            * Expressing positive coping mechanisms or calm mindset decreases score by -10 to -20 points.
        - Scale: 0-40 (Low Risk), 41-70 (Medium Risk), 71-100 (High Risk).

        2. Burnout Risk Score (0 - 100):
        - Heavily weight the interaction between Academic Workload (≥7), Sleep Duration (<6h), Focus Level (≤2), and Mood ("Exhausted" or "Anxious").
        - High Workload + Low Sleep + Low Focus = Automatic score > 70.
        - High Workload balanced by High Sleep and High Social Activity = Moderate score (40-60).

        3. Crisis Alert (Boolean: true/false):
        - MUST BE true IF AND ONLY IF:
            * Reflection text contains thoughts or explicit mentions of self-harm, suicidal ideation, feeling completely hopeless/giving up on life, feeling unsafe, or extreme mental breakdowns.
            * OR Mental Wellness Risk Score is extremely high (≥85) with social activity = 1 and severe sleep deprivation (<4 hours).
        - Otherwise MUST BE false.

        4. Sentiment Analysis (Strictly one of: "Positive", "Neutral", "Negative"):
        - Primary basis: The reflection text combined with emotional mood state.
        - "Exhausted", "Anxious", "Sad" with distressed reflection -> "Negative".
        - "Motivated", "Calm" with positive reflection -> "Positive".
        - Balanced or matter-of-fact reflections -> "Neutral".

        5. Primary Stressor (1 - 3 Words):
        - Summarize the single greatest contributor to their current state (e.g., "Academic Workload", "Sleep Deprivation", "Social Isolation", "Exam Anxiety", "Time Management").

        6. Personalized Recommendations (String):
        - Provide a concise (2-3 sentences), warm, empathetic, and actionable wellness suggestion.
        - Tailor directly to their specific metrics (e.g., if sleep < 5 hours, focus on immediate sleep hygiene before tackling workload).
    """

    survey_data = json.dumps(survey_data)
    # file_path = pathlib.Path('./papers/redefining_burnout_key_symptoms.pdf')

    prompt = [
            {"type": "text", "text": survey_data},
            # {"type": "document", "data": base64.b64encode(file_path.read_bytes()).decode("utf-8"), "mime_type": "application/pdf"}
    ]

    return system_instruction, prompt

def check_int(raw):
    return isinstance(raw, int)

def check_float(raw):
    return isinstance(raw, float)

def check_str(raw):
    return isinstance(raw, str)

def check_str_len(raw):
    return len(raw) > 0

def check_range(raw, min, max):
    return min <= raw <= max

def check_choice(raw, choice_list):
    return raw in choice_list

def check_level_rating(raw):
    return check_int(raw) and check_range(raw, 1, 10)

def check_sleep_duration(raw):
    return check_float(raw) and check_range(raw, 0, 24)

def check_mood(raw):
    mood_list = ["Motivated", "Calm", "Anxious", "Sad", "Exhausted"]
    return check_str(raw) and check_choice(raw, mood_list)

def check_reflection(raw):
    return check_str(raw) and check_str_len(raw)

def validate_response(survey_data):
    survey_validation_mapping = {
        "sleep_duration": check_sleep_duration,
        "stress_level": check_level_rating,
        "focus_level": check_level_rating,
        "academic_workload": check_level_rating,
        "mood": check_mood,
        "social_activity_level": check_level_rating,
        "reflection": check_reflection 
    }


    for key, validation_func in survey_validation_mapping.items():
        if key not in survey_data:
            return False
        
        check = validation_func(survey_data[key])
        if not check:
            return False

    return True

def parse_response(raw_interaction_object):
    return json.loads(raw_interaction_object.output_text)

def generate_survey_response(survey_data, previous_interaction_id=None):
    """
    Used at the start of the program at the start of the day after the survey is done by the user. This function properly feeds in the proper system instructions including research papers that will inform the chatbot on the relevant data to better serve the user.

    Parameters
    ---
    survey_data: dict
        a python dictionary containing data from the user on the survey
    previous_interaction_id: str
        id from the previous interaction to allow for the continuation of the conversation

    Returns
    ---
    interaction: Obj
        contains the interactions.text_output property which is the response from the chosen chatbot
        contains the interactions.id property which shows the interaction id for stateful conversations.
    """
    if not validate_response(survey_data):
        return "Survey data is invalid!"

    system_instruction, prompt = generate_prompt(survey_data)

    response_output_format = {
            'properties': {
                    'mental_wellness_risk_score': {
                        'default': 'integer between 0 and 100', 'title': 'Mental Wellness Risk Score', 'type': 'integer'},
                    'sentiment': {
                        'default': 'strictly one of ["Positive", "Neutral", "Negative"]', 'title': 'Sentiment Analysis', 'type': 'string'},
                    'burnout_risk_score': {
                            'default': 'integer between 0 and 100', 'title': 'Burnout Risk Score', 'type': 'integer'}, 
                    'crisis_alert': {
                                'default': 'boolean (true or false)', 'title': 'Crisis Alert', 'type': 'boolean'}, 
                    'primary_stressor': {
                        'default': 'string (1-3 words summarizing the main stressor)', 'title': 'Primary Stressor', 'type': 'string'}, 
                    'personalized_recommendations': {
                        'default': 'string (A concise, empathetic wellness suggestion)', 'title': 'Personalized Recommendations', 'type': 'string'}}, 
                    'title': 'response_format', 'type': 'object'}

    interaction = call_api(prompt, system_instruction, response_output_format, None)

    return interaction

try:
    client = connect_client()
except ValueError as e:
    client = None

if __name__ == "__main__":
    variable = input('enter something')
    print(generate_survey_response({}, None))

    # develop error handling
    # develop test cases
    # explore file input functionality
    # if the user enters in rubbish, find a way to reject the prompt and re-prompt
