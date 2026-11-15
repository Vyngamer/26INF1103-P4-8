from google import genai
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ai_manager_helper.data_classes.api_result import APIResult
from ai_manager_helper.data_classes.survey_entity_schema import SurveyEntitySchema
from ai_manager_helper.data_classes.conversation import Conversation

import json

class IChatClient(ABC):
    @abstractmethod
    def connect_client(self) -> None:
        pass
    
    @abstractmethod
    def send_message(self, prompt: str, system_instruction: Optional[str] = None, json_response_schema: Optional[dict] = None) -> APIResult:
        pass

class ICounsellingStrategy(ABC):
    @abstractmethod
    def get_system_instruction(self) -> str:
        pass
    
    @abstractmethod
    def get_json_response_schema(self) -> dict:
        pass

class IMessage(ABC):
    @abstractmethod
    def asdict(self) -> dict:
        pass

class IChatRepository(ABC):
    @abstractmethod
    def add_message(self, message):
        pass

    @abstractmethod
    def logs(self):
        pass

class GeminiClient(IChatClient):
    def __init__(self, model: str) -> None:
        self.__model = model
        self.__client = None

    def connect_client(self) -> None:
        self.__client = genai.Client()

    def send_message(self, prompt: str, previous_interaction_id: str, system_instruction: Optional[str] = None, response_json_format: Optional[dict] = None) -> APIResult:
        try:
            interaction = self.__client.interactions.create(
                model=self.__model,
                input=prompt,
                system_instruction=system_instruction,
                previous_interaction_id=previous_interaction_id,
                response_format = {
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": response_json_format
            })

            return APIResult.ok(interaction.model_dump())

        except Exception as e:
            return APIResult.fail(e)

class GeminiClientWithFallback(IChatClient):
    def __init__(self, primary_model: IChatClient, fallback_model: IChatClient) -> None:
        self.__primary = primary_model
        self.__fallbak = fallback_model

    def connect_client(self) -> None:
        pass

    def send_message(self, prompt: str, previous_interaction_id: str, system_instruction: Optional[str] = None, response_json_format: Optional[dict] = None) -> APIResult:
        try:
            self.__primary.send_message(prompt, previous_interaction_id, response_json_format)

        except 
        

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

class EvaluateSurveyStrategy(ICounsellingStrategy):
    def get_system_instruction(self) -> str:
        return """
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
        """
    
    def get_json_response_schema(self) -> dict:
        return {"type": "object",
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
                    "personalized_recommendations"]}

class CounsellingStrategyFactory:
    @staticmethod
    def create_strategy(strategy_type:str) -> ICounsellingStrategy:
        strategies = {
                'survey': CollectSurveyStrategy,
                'evaluate': EvaluateSurveyStrategy
        }

        return strategies[strategy_type]()

class AIManager:
    def __init__(self, client: IChatClient, conversation: IChatRepository) -> None:
        self.__client = client
        self.__conversation = conversation
        self.__previous_interaction_id = None
        self.__instruction_flag = True
        self.__survey_results = None
    
    def process_message(self, prompt: str, strategy: ICounsellingStrategy) -> dict:
        self.__conversation.add_message('user', 'YT', prompt)

        system_instruction = ""
        if self.__instruction_flag:
            system_instruction = strategy.get_system_instruction()
            self.__instruction_flag = False

        json_response_schema = strategy.get_json_response_schema()
        result = self.__client.send_message(prompt, self.__previous_interaction_id, system_instruction, json_response_schema)

        # Add error handling if error

        print(result)
        response = result.data
        self.__previous_interaction_id = response['id']
        self.__survey_results = json.loads(response['output_text'])
        ai_response = self.__survey_results['text']
        self.__conversation.add_message('ai', 'AI', ai_response)
        
        return {'text': ai_response, 'survey_done': self.__survey_results['survey_done']}
    
if __name__ == "__main__":
    api_client = GeminiClient('gemini-3.5-flash-lite')
    api_client.connect_client()
    conversation = Conversation()
    ai_manager = AIManager(api_client, conversation)
    collect_survey_strategy = CounsellingStrategyFactory.create_strategy('survey')
    print(ai_manager.process_message('Hello!', collect_survey_strategy)['text'])
