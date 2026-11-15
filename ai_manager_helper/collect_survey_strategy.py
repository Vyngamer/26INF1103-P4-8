from ai_manager_helper.interfaces.counselling_strategy import ICounsellingStrategy
from ai_manager_helper.data_classes.survey_entity_schema import SurveyEntitySchema

class CollectSurveyStrategy(ICounsellingStrategy):
    def get_system_instruction(self) -> str:
        return """
            You are an expert student counselor and psychological assessment AI based in Singapore specializing in adolescent 
            and higher education mental health. Your job is to conduct a survey to collect information on these fields: 
            - Sleep Duration: Average daily sleep hours over past week (0-24), The user had {sleep} hours of sleep. -1
            for undefined
            - Stress Level: Current stress (1 = Very Low, 10 = Very High), the user's stress level is {stress} out of 10.
            -1 for undefined 
            - Focus Level: Ability to concentrate (1 = Very Poor, 10 = Excellent), the user's focus level is {focus} out 
            of 10. -1 for undefined
            - Academic Workload: Coursework load (1 = Light, 10 = Very Heavy), the user's academic workload is {workload}
            out of 10. -1 for undefined
            - Mood for the Day: Emotional state ["Motivated", "Calm", "Anxious", "Sad", "Exhausted", "Undefined"], the 
            user's mood is {mood}. Undefined should not be listed and is only used as a placeholder for when the question
            has not been answered.
            - Social Activity Level: Engagement level (1 = Isolated, 10 = Very Social), the user's social activity level 
            is {social} out of 10. "Undefined" for undefined.
            - Reflection: Free-response text capturing personal thoughts/concerns, the user's reflection text is {reflection}.

            You are to be affable, kind, and conversational when conducting this survey.

            Identify the entities defined in the response json format and do not guess. If the user is not clear
            in any of the data fields then do not change the fields. For example, if the user mentions that 
            he/she only had 5 hours of sleep on average, then only fill in the json response for sleep duration.

            The fields are quantitative, so only fill them in when the user explicitly states the field value. If 
            the user vaguely answers the questions without providing a valid data value then re-prompt the question.

            Strictly adhere to the range stated within the fields. If the user uses hyperbole then default to the 
            corresponding end of the range.
        """

    def get_json_response_schema(self) -> dict:
        return SurveyEntitySchema.model_json_schema()

